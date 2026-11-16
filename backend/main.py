
from fastapi import FastAPI

from backend.routers.environmental_context import router as environmental_context_router
from backend.routers.land_cover import router as land_cover_router
from backend.routers.district_overview import router as district_overview_router

app = FastAPI(
    title="AranyaDrishti API",
    description="Environmental context services for Uttarakhand districts",
    version="1.0.0"
)

# Register API routes
app.include_router(environmental_context_router)
app.include_router(land_cover_router)
app.include_router(district_overview_router)


@app.get("/")
def root():
    return {
        "message": "AranyaDrishti API is running"
    }
