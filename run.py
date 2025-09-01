from app.core.logging_config import setup_logging
setup_logging()
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_config=None, log_level="debug")
