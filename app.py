from app.main import app

# Esta línea es necesaria para que Render encuentre la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
