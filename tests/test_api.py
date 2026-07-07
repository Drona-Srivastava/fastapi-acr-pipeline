import pytest

from fastapi.testclient import TestClient

from app.main import app, items


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_items():
    items.clear()

    yield

    items.clear()


def test_root():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "FastAPI application is running"
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy"
    }


def test_get_empty_items():
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == {}


def test_create_item():
    response = client.post(
        "/items/1",
        json={
            "name": "Keyboard",
            "price": 1500,
        },
    )

    assert response.status_code == 201

    assert response.json() == {
        "name": "Keyboard",
        "price": 1500.0,
    }


def test_get_item():
    client.post(
        "/items/1",
        json={
            "name": "Mouse",
            "price": 500,
        },
    )

    response = client.get("/items/1")

    assert response.status_code == 200

    assert response.json() == {
        "name": "Mouse",
        "price": 500.0,
    }


def test_get_missing_item():
    response = client.get("/items/999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Item not found"
    }


def test_duplicate_item():
    payload = {
        "name": "Monitor",
        "price": 10000,
    }

    client.post("/items/1", json=payload)

    response = client.post(
        "/items/1",
        json=payload,
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Item already exists"
    }


def test_delete_item():
    client.post(
        "/items/1",
        json={
            "name": "Laptop",
            "price": 60000,
        },
    )

    response = client.delete("/items/1")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Item deleted"
    }


def test_delete_missing_item():
    response = client.delete("/items/999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Item not found"
    }