from fastapi import FastAPI
from app.api.routes import upload, data, health

app = FastAPI(title="****** ARGUS Backend API ******")

# Include routers
app.include_router(upload.router, prefix="/upload", tags=["Upload"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(health.router, prefix="/health", tags=["Health"])
