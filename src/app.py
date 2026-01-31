from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config.config_manager import get_config_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load configuration on startup
    try:
        config_manager = get_config_manager()
        config_manager.initialize()
        config = config_manager.get_config()
        print(f"Successfully loaded configuration for: {config.app_name} ({config.environment})")
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        raise e
    
    yield
    
    # Clean up resources on shutdown if needed
    pass

app = FastAPI(
    title="Agentic Judge API",
    description="FastAPI application with LangChain and LangGraph integration",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Agentic Judge API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
