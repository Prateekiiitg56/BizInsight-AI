import uvicorn
from rag_api.api import app

# This file is the entry point to run the FastAPI server. It imports the `app` instance from `api.py` and starts the server using Uvicorn.
if __name__ == "__main__":
    uvicorn.run(
        "rag_api.api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,         
        log_level="info"
    )