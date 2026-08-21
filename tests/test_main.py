from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client



def create_user_and_get_token(
    client: TestClient,
    email: str,
    password: str,
) -> str:
    """
    Create a user and return its JWT access token.
    """
    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201, register_response.text
    assert register_response.json()["email"] == email

    login_response = client.post(
        "/auth/token",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200, login_response.text

    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]

    return token_data["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Create the Authorization header for protected endpoints."""
    return {"Authorization": f"Bearer {token}"}


def test_root_endpoint(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"message": "Welcome to DocFlow API"}


def test_register_login_and_read_current_user(client: TestClient):
    unique_id = uuid4().hex
    email = f"auth_{unique_id}@example.com"
    password = "StrongPassword123!"

    token = create_user_and_get_token(client, email, password)

    me_response = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    assert me_response.status_code == 200, me_response.text

    user_data = me_response.json()
    assert user_data["email"] == email
    assert "id" in user_data


def test_login_with_wrong_password_returns_401(client: TestClient):
    unique_id = uuid4().hex
    email = f"wrong_password_{unique_id}@example.com"
    correct_password = "CorrectPassword123!"

    create_user_and_get_token(client, email, correct_password)

    response = client.post(
        "/auth/token",
        data={
            "username": email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_protected_endpoint_requires_token(client: TestClient):
    response = client.get("/documents/")

    assert response.status_code == 401


def test_document_full_lifecycle(client: TestClient, monkeypatch):
    """
    Test the complete document lifecycle:

    upload -> list -> get -> status -> download -> delete

    Celery is mocked, so this test does not send a task to Redis.
    """
    fake_task = SimpleNamespace(id=f"test-task-{uuid4().hex}")

    monkeypatch.setattr(
        main_module,
        "process_document",
        SimpleNamespace(delay=lambda document_id: fake_task),
    )

    unique_id = uuid4().hex

    owner_email = f"owner_{unique_id}@example.com"
    owner_password = "OwnerPassword123!"
    owner_token = create_user_and_get_token(
        client,
        owner_email,
        owner_password,
    )
    owner_headers = auth_headers(owner_token)

    other_email = f"other_{unique_id}@example.com"
    other_password = "OtherPassword123!"
    other_token = create_user_and_get_token(
        client,
        other_email,
        other_password,
    )
    other_headers = auth_headers(other_token)

    filename = "test_document.txt"
    file_content = b"DocFlow automated test file content."

    # 1. Upload
    upload_response = client.post(
        "/documents/upload",
        headers=owner_headers,
        files={
            "file": (
                filename,
                file_content,
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 201, upload_response.text

    uploaded_document = upload_response.json()
    document_id = uploaded_document["id"]

    assert uploaded_document["filename"] == filename
    assert uploaded_document["status"] == "pending"
    assert uploaded_document["task_id"] == fake_task.id
    assert uploaded_document["file_size"] == len(file_content)
    assert uploaded_document["content_type"] == "text/plain"
    assert uploaded_document["error_message"] is None
    assert uploaded_document["processed_at"] is None

    # 2. List
    list_response = client.get(
        "/documents/",
        headers=owner_headers,
    )

    assert list_response.status_code == 200, list_response.text
    documents = list_response.json()
    assert any(document["id"] == document_id for document in documents)

    # 3. Get metadata
    get_response = client.get(
        f"/documents/{document_id}",
        headers=owner_headers,
    )

    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["id"] == document_id
    assert get_response.json()["filename"] == filename

    # 4. Get status
    status_response = client.get(
        f"/documents/{document_id}/status",
        headers=owner_headers,
    )

    assert status_response.status_code == 200, status_response.text
    assert status_response.json() == {
        "document_id": document_id,
        "status": "pending",
    }

    # 5. Download
    download_response = client.get(
        f"/documents/{document_id}/download",
        headers=owner_headers,
    )

    assert download_response.status_code == 200, download_response.text
    assert download_response.content == file_content
    assert "attachment" in download_response.headers["content-disposition"]
    assert filename in download_response.headers["content-disposition"]

    # 6. Access-control check
    unauthorized_get_response = client.get(
        f"/documents/{document_id}",
        headers=other_headers,
    )

    assert unauthorized_get_response.status_code == 404
    assert unauthorized_get_response.json()["detail"] == "Document not found"

    # 7. Delete
    delete_response = client.delete(
        f"/documents/{document_id}",
        headers=owner_headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    # 8. Confirm deletion
    get_after_delete_response = client.get(
        f"/documents/{document_id}",
        headers=owner_headers,
    )

    assert get_after_delete_response.status_code == 404
    assert get_after_delete_response.json()["detail"] == "Document not found"
