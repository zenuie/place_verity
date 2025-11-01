# veritas_app/api/endpoints.py
from fastapi import APIRouter, HTTPException, Request
from app.models.schemas import (
    ManualFetchRequest, ReviewApproveRequest, LockStatusResponse,
    SuccessResponse, VerificationReport, ErrorDetail
)
from app.services import verification
from app.storage import db

router = APIRouter()


@router.get("/status/global", response_model=LockStatusResponse, tags=["Status"])
def get_global_status():
    return db.get_lock_status("global")


@router.get("/status/place/{place_id}", response_model=LockStatusResponse, tags=["Status"])
def get_place_status(place_id: str):
    return db.get_lock_status(place_id)


@router.post(
    "/manual/fetch",
    response_model=VerificationReport,
    responses={409: {"model": ErrorDetail}, 404: {"model": ErrorDetail}, 500: {"model": ErrorDetail}},
    tags=["Manual Flow"]
)
async def manual_fetch(request: Request, payload: ManualFetchRequest):
    """(Async) Manually triggers the verification flow for a single place."""
    place_id = payload.place_id
    if not db.acquire_lock(place_id):
        raise HTTPException(status_code=409, detail="Verification already in progress for this place.")

    try:
        place_data = db.get_place_by_id(place_id)
        if not place_data:
            raise HTTPException(status_code=404, detail="Place not found.")

        # Access shared clients via request.app.state
        clients = request.app.state.api_clients
        query = f"{place_data.get('name', '')} {place_data.get('address', '')}"
        search_results = await verification.google_search(clients.httpx_client, query)

        if not search_results:
            raise HTTPException(status_code=404, detail="Could not find information for this place online.")

        report = await verification.get_llm_report(clients.openai_client, place_data, search_results)
        if not report:
            raise HTTPException(status_code=500, detail="Failed to generate verification report from LLM.")

        return report
    finally:
        db.release_lock(place_id)

# ... Other endpoints (review_approve, auto_trigger, etc.) go here ...
# They will need to be adapted to use the router and access clients from request.app.state
