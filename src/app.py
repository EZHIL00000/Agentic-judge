from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.managers.config_manager import get_config_manager

from src.utils import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load configuration on startup
    try:
        logger.info("Initializing application configuration...")
        config_manager = get_config_manager()
        config_manager.initialize()
        config = config_manager.get_config()
        logger.info(f"Successfully loaded configuration for: {config.app_name} ({config.environment})")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise e
    
    yield
    
    # Clean up resources on shutdown if needed
    pass

from src.routers import game_router

app = FastAPI(
    title="Agentic Judge API",
    description="FastAPI application with LangChain and LangGraph integration",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(game_router.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Agentic Judge API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
