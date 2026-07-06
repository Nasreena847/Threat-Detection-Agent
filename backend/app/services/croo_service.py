class CrooService:
    """Isolated CROO integration boundary with mocked MVP responses."""

    def discover_agents(self) -> list[dict[str, object]]:
        return [
            {
                "id": "threat-intel-agent",
                "name": "Threat Intelligence Agent",
                "description": "Mock agent reserved for external threat intelligence enrichment.",
                "available": False,
            },
            {
                "id": "privacy-audit-agent",
                "name": "Privacy Audit Agent",
                "description": "Mock agent reserved for tracker and privacy signal enrichment.",
                "available": False,
            },
        ]

    def invoke_agent(self, agent_id: str, payload: dict[str, object]) -> dict[str, object]:
        return {
            "agent_id": agent_id,
            "status": "mocked",
            "message": "CROO SDK integration is isolated and ready for a future implementation.",
            "received_keys": sorted(payload.keys()),
        }


croo_service = CrooService()
