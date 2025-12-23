from fastapi import FastAPI
from dotenv import load_dotenv
from chat_service.main import stream
from nureg_search.main import nureg_search
from configuration import configure_telemetry
from reportability_manual_search.main import reportability_manual_search
from health.main import health_router

load_dotenv()
configure_telemetry()

app = FastAPI(debug=True)
app.include_router(stream, prefix="/chat", tags=["chat"])
app.include_router(nureg_search, prefix="/search", tags=["search"])
app.include_router(reportability_manual_search, prefix="/search", tags=["search"])
app.include_router(health_router, tags=["health"])
