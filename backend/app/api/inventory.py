
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import (
    Batch,
    BatchInventory,
    InventoryEvent,
    Product,
    Shelf,
)
from app.schemas.inventory import (
    InventoryAdjust,
    InventoryEventOut,
    InventoryOut,
    InventoryReceive,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


def inventory_to_dict(entry, batch, product, shelf):
    return {
        "id": entry.id,
        "batch_id": entry.batch_id,
        "shelf_id": entry.shelf_id,
        "product_id": product.id,
        "product_name": product.name,
        "batch_number": batch.batch_number,
        "shelf_code": shelf.code,
        "shelf_name": shelf.name,
        "quantity": entry.quantity,
        "updated_at": entry.updated_at,
    }


@router.get("/", response_model=list[InventoryOut])
def list_inventory(
    shelf_id: int | None = Query(default=None, gt=0),
    batch_id: int | None = Query(default=None, gt=0),
    product_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    statement = (
        select(BatchInventory, Batch, Product, Shelf)
        .join(Batch, Batch.id == BatchInventory.batch_id)
        .join(Product, Product.id == Batch.product_id)
        .join(Shelf, Shelf.id == BatchInventory.shelf_id)
    )

    if shelf_id is not None:
        statement = statement.where(
            BatchInventory.shelf_id == shelf_id
        )

    if batch_id is not None:
        statement = statement.where(
            BatchInventory.batch_id == batch_id
        )

    if product_id is not None:
        statement = statement.where(
            Batch.product_id == product_id
        )

    rows = db.execute(
        statement.order_by(Product.name, Batch.expiration_date)
    ).all()

    return [
        inventory_to_dict(entry, batch, product, shelf)
        for entry, batch, product, shelf in rows
    ]


@router.post(
    "/receive",
    response_model=InventoryOut,
    status_code=status.HTTP_201_CREATED,
)
def receive_stock(
    data: InventoryReceive,
    db: Session = Depends(get_db),
):
    batch = db.get(Batch, data.batch_id)

    if batch is None:
        raise HTTPException(status_code=404, detail="Batch not found.")

    shelf = db.get(Shelf, data.shelf_id)

    if shelf is None:
        raise HTTPException(status_code=404, detail="Shelf not found.")

    if not shelf.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot receive stock into an inactive shelf.",
        )

    try:
        entry = db.scalar(
            select(BatchInventory)
            .where(
                BatchInventory.batch_id == data.batch_id,
                BatchInventory.shelf_id == data.shelf_id,
            )
            .with_for_update()
        )

        if entry is None:
            entry = BatchInventory(
                batch_id=data.batch_id,
                shelf_id=data.shelf_id,
                quantity=data.quantity,
            )
            db.add(entry)
            db.flush()
        else:
            entry.quantity += data.quantity
            db.flush()

        event = InventoryEvent(
            product_id=batch.product_id,
            batch_id=batch.id,
            shelf_id=shelf.id,
            event_type="RESTOCK",
            quantity_change=data.quantity,
            quantity_after=entry.quantity,
            source="MANUAL",
            notes=data.notes,
        )

        db.add(event)
        db.commit()
        db.refresh(entry)

        product = db.get(Product, batch.product_id)

        return inventory_to_dict(entry, batch, product, shelf)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Inventory entry could not be created. "
                "The batch/shelf combination may have been modified "
                "concurrently. Please retry."
            ),
        )


@router.post(
    "/{inventory_id}/adjust",
    response_model=InventoryOut,
)
def adjust_inventory(
    inventory_id: int,
    data: InventoryAdjust,
    db: Session = Depends(get_db),
):
    entry = db.scalar(
        select(BatchInventory)
        .where(BatchInventory.id == inventory_id)
        .with_for_update()
    )

    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory entry not found.",
        )

    difference = data.new_quantity - entry.quantity

    if difference == 0:
        raise HTTPException(
            status_code=400,
            detail="The new quantity is identical to the current quantity.",
        )

    batch = db.get(Batch, entry.batch_id)
    shelf = db.get(Shelf, entry.shelf_id)

    if shelf is None:
        raise HTTPException(status_code=404, detail="Shelf not found.")

    entry.quantity = data.new_quantity

    event = InventoryEvent(
        product_id=batch.product_id,
        batch_id=batch.id,
        shelf_id=shelf.id,
        event_type="ADJUSTMENT",
        quantity_change=difference,
        quantity_after=data.new_quantity,
        source="MANUAL",
        notes=data.notes,
    )

    db.add(event)
    db.commit()
    db.refresh(entry)

    product = db.get(Product, batch.product_id)

    return inventory_to_dict(entry, batch, product, shelf)


@router.get("/events", response_model=list[InventoryEventOut])
def list_inventory_events(
    product_id: int | None = Query(default=None, gt=0),
    batch_id: int | None = Query(default=None, gt=0),
    shelf_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    statement = select(InventoryEvent)

    if product_id is not None:
        statement = statement.where(
            InventoryEvent.product_id == product_id
        )

    if batch_id is not None:
        statement = statement.where(
            InventoryEvent.batch_id == batch_id
        )

    if shelf_id is not None:
        statement = statement.where(
            InventoryEvent.shelf_id == shelf_id
        )

    statement = statement.order_by(
        InventoryEvent.occurred_at.desc()
    )

    return db.scalars(statement).all()
