import asyncio
from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.models import Document
from app.workers.celery_app import celery_app


async def _process_document_async(document_id: int):
    """Async helper to process document and update database status."""
    async with AsyncSessionLocal() as session:
        # Fetch target document
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return f"Document {document_id} not found"

        # Mark document as processing
        document.status = "processing"
        await session.commit()

        # Simulate processing workload
        await asyncio.sleep(5)

        # Mark document as completed
        document.status = "completed"
        await session.commit()

        return f"Document {document_id} processed successfully"


@celery_app.task
def test_task():
    """Simple test task to verify Celery worker connectivity."""
    return "Celery is working!"


@celery_app.task
def process_document(document_id: int):
    """Celery task entrypoint handling event loop and connection cleanup."""
    async def _runner():
        try:
            return await _process_document_async(document_id)
        finally:
            # Clean up connection pool for this event loop
            await engine.dispose()

    return asyncio.run(_runner())
