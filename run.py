import uvicorn
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Changed from "app.api:app"
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )