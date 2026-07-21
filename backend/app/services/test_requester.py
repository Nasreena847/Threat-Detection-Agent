import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

try:
    from croo import AgentClient, Config
    from croo.types import NegotiateOrderRequest
except ModuleNotFoundError:  # Allows local import/tests without the CROO SDK installed.
    class _MissingCrooSDK:
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("CROO SDK is not installed. Install the croo package to test negotiation.")

    AgentClient = _MissingCrooSDK
    Config = _MissingCrooSDK

    @dataclass(frozen=True)
    class NegotiateOrderRequest:
        service_id: str
        requirements: str
        metadata: str = ""


logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 2
TIMEOUT_SECONDS = 60


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _derive_ws_url(base_url: str) -> str:
    if base_url.startswith("https://"):
        return base_url.replace("https://", "wss://", 1).rstrip("/") + "/ws"
    if base_url.startswith("http://"):
        return base_url.replace("http://", "ws://", 1).rstrip("/") + "/ws"
    return base_url.rstrip("/") + "/ws"


def _read_attr(value: Any, *names: str) -> Any:
    if isinstance(value, dict):
        for name in names:
            if name in value:
                return value[name]
        return None

    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _status_name(value: Any) -> str:
    status = _read_attr(value, "status", "state")
    enum_value = _read_attr(status, "value")
    if enum_value is not None:
        return str(enum_value).lower()
    if status is None:
        return ""
    return str(status).split(".")[-1].lower()


def _negotiation_id(value: Any) -> str:
    negotiation_id = _read_attr(value, "negotiation_id", "negotiationId", "id")
    return str(negotiation_id or "").strip()


def _order_id(value: Any) -> str:
    order_id = _read_attr(value, "order_id", "orderId")
    if order_id:
        return str(order_id).strip()

    order = _read_attr(value, "order")
    nested_order_id = _read_attr(order, "order_id", "orderId", "id")
    return str(nested_order_id or "").strip()


async def run_requester(target_url: str) -> None:
    base_url = _required_env("CROO_BASE_URL")
    requester_api_key = _required_env("CROO_REQUESTER_API_KEY")
    service_id = _required_env("CROO_SERVICE_ID")

    config = Config(base_url=base_url, ws_url=_derive_ws_url(base_url))
    client = AgentClient(config, requester_api_key)
    requirements = json.dumps({"url": target_url})

    logger.info("Negotiating with service_id=%s for url=%s", service_id, target_url)
    try:
        negotiation = await client.negotiate_order(
            NegotiateOrderRequest(
                service_id=service_id,
                requirements=requirements,
                metadata=requirements,
            )
        )
    except Exception as exc:
        message = str(exc)
        if "cannot negotiate own service" in message.lower():
            raise RuntimeError(
                "CROO rejected the negotiation because CROO_REQUESTER_API_KEY belongs to the same "
                "identity that owns CROO_SERVICE_ID. Create or use a second CROO agent/API key as the "
                "requester, keep CROO_SERVICE_ID set to the Threat Detection Agent service id, then retry."
            ) from exc
        if "provider_not_accepting_orders" in message.lower() or "provider is not accepting new orders" in message.lower():
            raise RuntimeError(
                "CROO says the provider is not accepting new orders. Start the provider in another "
                "terminal with CROO_API_KEY set to the service owner's key and run: "
                "python -m app.services.croo_provider. Confirm it prints started: True before retrying."
            ) from exc
        raise

    negotiation_id = _negotiation_id(negotiation)
    if not negotiation_id:
        raise RuntimeError(f"CROO negotiation response did not include a negotiation id: {negotiation!r}")

    logger.info("Created negotiation_id=%s", negotiation_id)
    deadline = asyncio.get_running_loop().time() + TIMEOUT_SECONDS

    while True:
        current = await client.get_negotiation(negotiation_id)
        status = _status_name(current)
        print(f"negotiation_id={negotiation_id} status={status or 'unknown'}")

        if status == "accepted":
            order_id = _order_id(current)
            print("SUCCESS: negotiation accepted")
            print("negotiation_id:", negotiation_id)
            print("order_id:", order_id or "not available")
            return

        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError(
                "Timed out waiting for negotiation to reach accepted status. "
                "Check that CrooProvider is running in another terminal with: "
                "python -m app.services.croo_provider"
            )

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    asyncio.run(run_requester(target))
