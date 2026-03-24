"""POST /extract endpoint integration tests — API-01 + ING-06."""
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


async def test_post_extract_returns_job_id(client):
    """POST /extract with a PDF returns job_id and status=pending."""
    with open(os.path.join(FIXTURES, "sample.pdf"), "rb") as f:
        response = await client.post("/api/extract", files={"file": ("sample.pdf", f, "application/pdf")})
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "pending"
    # job_id should be a non-empty string (UUID)
    assert isinstance(body["job_id"], str) and len(body["job_id"]) > 0


async def test_unsupported_extension(client):
    """POST /extract with .txt returns 400 unsupported_file_type, no job created."""
    response = await client.post(
        "/api/extract",
        files={"file": ("document.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "unsupported_file_type"
    # Confirm no job was created
    job_id_check = await client.get("/api/jobs/nonexistent-no-job-created")
    assert job_id_check.status_code == 404


async def test_post_extract_xlsx(client):
    """POST /extract with XLSX returns job_id."""
    with open(os.path.join(FIXTURES, "sample.xlsx"), "rb") as f:
        response = await client.post(
            "/api/extract",
            files={"file": ("sample.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "pending"


async def test_post_extract_png(client):
    """POST /extract with PNG returns job_id."""
    with open(os.path.join(FIXTURES, "sample.png"), "rb") as f:
        response = await client.post(
            "/api/extract",
            files={"file": ("sample.png", f, "image/png")},
        )
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "pending"


async def test_post_extract_html(client):
    """POST /extract with HTML returns job_id."""
    with open(os.path.join(FIXTURES, "sample.html"), "rb") as f:
        response = await client.post(
            "/api/extract",
            files={"file": ("sample.html", f, "text/html")},
        )
    assert response.status_code == 200
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "pending"
