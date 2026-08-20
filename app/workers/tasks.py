import asyncio
import re
from collections import defaultdict
from pathlib import Path

import fitz
from docx import Document as DocxDocument
from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.models import Document
from app.workers.celery_app import celery_app


def clean_extracted_text(text: str) -> str:
    """Normalize extracted text."""
    text = re.sub(r"[\u200c\u200d]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,:؛،!?])", r"\1", text)
    return text.strip()


def contains_rtl_text(text: str) -> bool:
    """Check whether text contains RTL characters."""
    return bool(re.search(r"[\u0600-\u06FF]", text))


def extract_pdf_text(file_path: str) -> str:
    """Extract PDF text with RTL line ordering."""
    pdf = fitz.open(file_path)

    try:
        pages_text = []

        for page in pdf:
            words = page.get_text("words")
            lines = defaultdict(list)

            for word in words:
                x0, y0, x1, y1, text, block_no, line_no, word_no = word
                lines[(block_no, line_no)].append((x0, text))

            page_lines = []

            for line_words in lines.values():
                line_text = " ".join(text for _, text in line_words)

                if contains_rtl_text(line_text):
                    line_words.sort(key=lambda item: item[0], reverse=True)
                else:
                    line_words.sort(key=lambda item: item[0])

                page_lines.append(" ".join(text for _, text in line_words))

            pages_text.append("\n".join(page_lines))

        return "\n".join(pages_text)
    finally:
        pdf.close()


def extract_text(file_path: str) -> str:
    """Extract text based on file type."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        return extract_pdf_text(str(path))

    if suffix == ".docx":
        doc = DocxDocument(str(path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {suffix}")


async def _process_document_async(document_id: int):
    """Process a document and update its status."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return f"Document {document_id} not found"

        document.status = "processing"
        await session.commit()

        file_content = extract_text(document.file_path)
        cleaned_content = clean_extracted_text(file_content)

        document.status = "completed"
        await session.commit()

        return {
            "document_id": document_id,
            "status": document.status,
            "result": {
                "text": cleaned_content,
                "character_count": len(cleaned_content),
                "word_count": len(cleaned_content.split()),
            },
        }


@celery_app.task
def test_task():
    """Verify Celery worker connectivity."""
    return "Celery is working!"


@celery_app.task
def process_document(document_id: int):
    """Run document processing in Celery."""

    async def _runner():
        try:
            return await _process_document_async(document_id)
        finally:
            await engine.dispose()

    return asyncio.run(_runner())
