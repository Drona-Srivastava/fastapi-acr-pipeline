import pytest

from fastapi.testclient import TestClient

from app.main import app, url_store


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_url_store():
    url_store.clear()

    yield

    url_store.clear()


def create_test_url(url: str = "https://example.com"):
    response = client.post(
        "/urls",
        json={
            "url": url,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "service": "URL Shortener API",
        "version": "1.0.0",
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "service": "url-shortener",
        "version": "1.0.0",
    }


def test_create_short_url():
    response = client.post(
        "/urls",
        json={
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert "short_code" in body
    assert "short_url" in body

    assert body["original_url"] == "https://example.com/"


def test_create_invalid_url():
    response = client.post(
        "/urls",
        json={
            "url": "not-a-valid-url",
        },
    )

    assert response.status_code == 422


def test_list_urls():
    created = create_test_url()

    response = client.get("/urls")

    assert response.status_code == 200

    body = response.json()

    assert created["short_code"] in body


def test_get_url_info():
    created = create_test_url()

    short_code = created["short_code"]

    response = client.get(
        f"/urls/{short_code}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "short_code": short_code,
        "original_url": "https://example.com/",
        "clicks": 0,
    }


def test_get_missing_url():
    response = client.get(
        "/urls/not-found"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Short URL not found"
    }


def test_redirect():
    created = create_test_url()

    short_code = created["short_code"]

    response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert response.status_code == 307

    assert response.headers["location"] == (
        "https://example.com/"
    )


def test_redirect_increments_clicks():
    created = create_test_url()

    short_code = created["short_code"]

    client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    response = client.get(
        f"/urls/{short_code}"
    )

    assert response.json()["clicks"] == 2


def test_missing_redirect():
    response = client.get(
        "/does-not-exist",
        follow_redirects=False,
    )

    assert response.status_code == 404


def test_delete_short_url():
    created = create_test_url()

    short_code = created["short_code"]

    response = client.delete(
        f"/urls/{short_code}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Short URL deleted"
    }


def test_deleted_url_is_not_accessible():
    created = create_test_url()

    short_code = created["short_code"]

    client.delete(
        f"/urls/{short_code}"
    )

    response = client.get(
        f"/urls/{short_code}"
    )

    assert response.status_code == 404