from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="FastAPI ACR Pipeline Demo",
    version="1.0.0",
)


class Item(BaseModel):
    name: str
    price: float


items: dict[int, Item] = {}


@app.get("/")
def root():
    return {
        "message": "FastAPI application is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/items")
def get_items():
    return items


@app.get("/items/{item_id}")
def get_item(item_id: int):
    item = items.get(item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
        )

    return item


@app.post("/items/{item_id}", status_code=201)
def create_item(item_id: int, item: Item):
    if item_id in items:
        raise HTTPException(
            status_code=409,
            detail="Item already exists",
        )

    items[item_id] = item

    return item


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    if item_id not in items:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
        )

    del items[item_id]

    return {
        "message": "Item deleted"
    }