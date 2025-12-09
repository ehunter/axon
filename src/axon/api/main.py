"""FastAPI application for Axon Brain Bank Discovery System."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from axon.api.routes import chat, samples

app = FastAPI(
    title="Axon Brain Bank API",
    description="API for discovering and querying brain tissue samples across multiple brain banks.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(samples.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "axon"}


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Axon Brain Bank API",
        "version": "0.1.0",
        "docs": "/docs",
    }

