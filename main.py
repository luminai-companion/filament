import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app", host="0.0.0.0", port=9000, reload=False, log_level="info"
    )
