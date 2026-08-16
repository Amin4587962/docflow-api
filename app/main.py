from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "DocFlow API is running successfully!"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check database connection."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "unhealthy", "database": "disconnected"}
