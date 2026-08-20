import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from api.routes import app  # noqa: F401 — exportado para uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("🚀 AromaBot arrancando...")
    uvicorn.run(app, host="0.0.0.0", port=port)
