import asyncio
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Document
from app.workers.celery_app import celery_app


async def _process_document_async(document_id: int):
    """Async helper to simulate document processing and update status."""
    async with AsyncSessionLocal() as session:
        # Fetch document by id
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return f"Document {document_id} not found"

        # Update status to processing
        document.status = "processing"
        await session.commit()

        # Simulate heavy processing work
        await asyncio.sleep(5)

        # Update status to completed
        document.status = "completed"
        await session.commit()

        return f"Document {document_id} processed successfully"


@celery_app.task
def test_task():
    """Simple test task to verify Celery worker connectivity."""
    return "Celery is working!"


@celery_app.task
def process_document(document_id: int):
    """Celery task entrypoint for document processing."""
    return asyncio.run(_process_document_async(document_id))
