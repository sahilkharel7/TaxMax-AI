"""/api/documents/extract is a documented safe stub.

Until real document extraction lands, the endpoint must:
- Return a controlled, schema-valid response (not crash) for supported types.
- Reject unsupported document types with 422.
- Make it explicit that extracted fields are not filing-ready.
- Never leak filesystem paths or secrets.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _post(document: dict) -> dict:
    response = client.post("/api/documents/extract", json={"document": document} if "document" not in document else document)
    return {"status_code": response.status_code, "json": response.json(), "text": response.text}


def test_extract_accepts_w2_metadata_as_safe_stub() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "w2",
            "file_name": "sample-w2.pdf",
            "extraction_status": "needs_review",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_required"
    assert "not available" in payload["message"].lower()
    assert any(
        warning["code"] == "DOCUMENT_EXTRACTION_NOT_AVAILABLE"
        for warning in payload["warnings"]
    )
    assert payload["document"]["document_type"] == "w2"
    assert "Confirmed document fields" in payload["missing_information"]
    assert payload["disclaimer"]
    assert "filing-ready" in payload["disclaimer"].lower()


def test_extract_accepts_1098_t_metadata() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "1098_t",
            "file_name": "sample-1098t.pdf",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document"]["document_type"] == "1098_t"


def test_extract_rejects_unsupported_document_type() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "k1_partnership",
            "file_name": "k1.pdf",
        },
    )

    assert response.status_code == 422


def test_extract_rejects_unsupported_file_extension() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "w2",
            "file_name": "sample.exe",
        },
    )

    assert response.status_code == 422


def test_extract_rejects_oversized_file() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "w2",
            "file_name": "sample.pdf",
            "file_size_bytes": 26 * 1024 * 1024,
        },
    )

    assert response.status_code == 413


def test_extract_rejects_missing_document_type() -> None:
    response = client.post(
        "/api/documents/extract",
        json={"file_name": "mystery.pdf"},
    )

    assert response.status_code == 422


def test_extract_rejects_empty_body() -> None:
    response = client.post("/api/documents/extract", json={})

    assert response.status_code == 422


def test_extract_handles_other_document_type_safely() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "other",
            "file_name": "scan.pdf",
            "notes": "Unknown form, manual review required.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_required"


def test_extract_does_not_pretend_to_extract_real_values() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "w2",
            "file_name": "sample-w2.pdf",
            "extracted_fields": {"wages": "999999.99"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_required"
    forbidden_phrases = (
        "extraction succeeded",
        "extracted successfully",
        "filing-ready values",
        "ready to file",
    )
    text = payload["message"].lower() + " " + payload["disclaimer"].lower()
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_extract_response_does_not_leak_filesystem_paths() -> None:
    response = client.post(
        "/api/documents/extract",
        json={
            "document_type": "w2",
            "file_name": "sample-w2.pdf",
        },
    )

    body_text = response.text
    forbidden_fragments = ["/Users/", "/home/", "site-packages", ".venv/"]
    for fragment in forbidden_fragments:
        assert fragment not in body_text
