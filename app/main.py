import os
import shutil
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Document, User
from app.schemas import DocumentResponse, Token, UserCreate, UserResponse
from app.workers.tasks import process_document

# Ensure upload directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="DocFlow API")


@app.get("/")
async def root():
    return {"message": "Welcome to DocFlow API"}


# --- Auth Endpoints ---

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    new_user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.post("/auth/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return an access token."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


# --- Document Endpoints ---

@app.post(
    "/documents/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a new document for the authenticated user and trigger processing."""
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_upload_dir / file.filename

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_path)

    # Save metadata to database
    new_doc = Document(
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        content_type=file.content_type or "application/octet-stream",
        owner_id=current_user.id,
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    # Trigger background processing task
    process_document.delay(new_doc.id)

    return new_doc


@app.get("/documents/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all documents owned by the authenticated user with pagination."""
    query = (
        select(Document)
        .where(Document.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    documents = result.scalars().all()
    return documents


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get metadata of a specific document owned by the authenticated user."""
    query = select(Document).where(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    )
    result = await db.execute(query)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@app.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the actual document file."""
    query = select(Document).where(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    )
    result = await db.execute(query)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=file_path,
        filename=doc.filename,
        media_type=doc.content_type,
    )


@app.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete document from database and remove its file from disk."""
    query = select(Document).where(
        Document.id == document_id,
        Document.owner_id == current_user.id,
    )
    result = await db.execute(query)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Remove physical file if present
    file_path = Path(doc.file_path)
    if file_path.exists():
        os.remove(file_path)

    # Delete record from database
    await db.delete(doc)
    await db.commit()

    return None
