from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

health_router = APIRouter()


@health_router.get("/", status_code=status.HTTP_200_OK)
def health_check() -> JSONResponse:
    """Health check endpoint.

    Returns:
        JSONResponse: Service health status.
    """
    return JSONResponse(content={"status": "ok"})
