from fastapi import APIRouter

from app.schemas.request import CrooInvokeRequest
from app.schemas.response import CrooAgentsResponse, CrooInvokeResponse
from app.services.croo_service import croo_service

router = APIRouter(prefix="/api/croo", tags=["CROO"])


@router.get("/agents", response_model=CrooAgentsResponse)
def discover_agents() -> CrooAgentsResponse:
    return CrooAgentsResponse(agents=croo_service.discover_agents())


@router.post("/invoke", response_model=CrooInvokeResponse)
def invoke_agent(request: CrooInvokeRequest) -> CrooInvokeResponse:
    response = croo_service.invoke_agent(request.agent_id, request.payload)
    return CrooInvokeResponse(
        agent_id=request.agent_id,
        invoked=True,
        response=response,
    )
