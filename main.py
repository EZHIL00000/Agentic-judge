import uvicorn
from src.app import app

if __name__ == "__main__":
    # Run the application using uvicorn
    # "src.app:app" points to the 'app' object in src/app.py
    # reload=True enables auto-reloading during development
    try:
        from src.utils import logger
        logger.info("Starting Agentic Judge API...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        from src.utils import logger
        logger.critical(f"Application failed to start: {e}")
        raise e
