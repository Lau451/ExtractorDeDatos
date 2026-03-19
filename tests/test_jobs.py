"""GET /jobs/{id} integration tests — API-02."""
import asyncio
import os
import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


async def test_get_nonexistent_job(client):
    """GET /jobs/<unknown-id> returns 404 with error=job_not_found."""
    response = await client.get("/jobs/nonexistent-id-that-does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "job_not_found"


async def test_job_lifecycle(client):
    """POST /extract with HTML, poll until complete, assert raw_text contains 'Test Document'."""
    with open(os.path.join(FIXTURES, "sample.html"), "rb") as f:
        post_response = await client.post(
            "/extract",
            files={"file": ("sample.html", f, "text/html")},
        )
    assert post_response.status_code == 200
    job_id = post_response.json()["job_id"]

    # Poll until terminal state (max 30s)
    deadline = asyncio.get_event_loop().time() + 30
    job = None
    while asyncio.get_event_loop().time() < deadline:
        get_response = await client.get(f"/jobs/{job_id}")
        assert get_response.status_code == 200
        job = get_response.json()
        if job["status"] not in ("pending", "processing"):
            break
        await asyncio.sleep(0.5)

    assert job is not None, "Job polling timed out"
    assert job["status"] == "complete", f"Expected complete, got: {job['status']} — error: {job.get('error_code')}: {job.get('error_message')}"
    assert job.get("result") is not None
    raw_text = job["result"]["raw_text"]
    assert isinstance(raw_text, str) and len(raw_text.strip()) > 0
    assert "Test Document" in raw_text
