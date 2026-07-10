from pydantic import BaseModel, Field


class AuditRequest(BaseModel):
    """Payload sent by the Chrome extension for the active tab."""

    url: str = Field(..., min_length=1, description="Current tab URL.")
    title: str = Field(default="", description="Current page title.")
    page_text: str = Field(default="", description="Visible text extracted by the extension.")
    html: str = Field(default="", description="Raw page HTML captured by the extension.")
    domain: str | None = Field(default=None, description="Current page domain if provided by the extension.")
    favicon: str | None = Field(default=None, description="Page favicon if provided by the extension.")
    https: bool | None = Field(default=None, description="Whether the URL uses HTTPS.")


class CrooInvokeRequest(BaseModel):
    """Request body for the CROO agent invocation endpoint."""

    agent_id: str = Field(..., min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
