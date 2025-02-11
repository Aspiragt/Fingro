import uvicorn
import os
from app.main import app

# Esta línea es necesaria para que Render encuentre la aplicación
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
