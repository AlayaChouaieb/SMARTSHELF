
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Shelf, BatchInventory
from app.schemas.shelf import ShelfCreate, ShelfOut, ShelfUpdate

router = APIRouter(prefix="/shelves", tags=["Shelves"])


@router.get("/", response_model=list[ShelfOut])
def list_shelves(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    statement = select(Shelf)

    if active_only:
        statement = statement.where(Shelf.is_active.is_(True))

    return db.scalars(statement.order_by(Shelf.code)).all()


@router.post(
    "/",
    response_model=ShelfOut,
    status_code=status.HTTP_201_CREATED,
)
def create_shelf(
    data: ShelfCreate,
    db: Session = Depends(get_db),
):
    shelf = Shelf(**data.model_dump())
    db.add(shelf)

    try:
        db.commit()
        db.refresh(shelf)
        return shelf

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Shelf code or device ID already exists.",
        )


@router.get("/{shelf_id}", response_model=ShelfOut)
def get_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
):
    shelf = db.get(Shelf, shelf_id)

    if shelf is None:
        raise HTTPException(status_code=404, detail="Shelf not found.")

    return shelf


@router.put("/{shelf_id}", response_model=ShelfOut)
def update_shelf(
    shelf_id: int,
    data: ShelfUpdate,
    db: Session = Depends(get_db),
):
    shelf = db.get(Shelf, shelf_id)

    if shelf is None:
        raise HTTPException(status_code=404, detail="Shelf not found.")

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(shelf, field, value)

    try:
        db.commit()
        db.refresh(shelf)
        return shelf

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Shelf code or device ID already exists.",
        )


@router.delete("/{shelf_id}")
def deactivate_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
):
    shelf = db.get(Shelf, shelf_id)

    if shelf is None:
        raise HTTPException(status_code=404, detail="Shelf not found.")

    if not shelf.is_active:
        return {"message": "Shelf is already inactive."}

    stock = db.scalar(
        select(BatchInventory.id)
        .where(
            BatchInventory.shelf_id == shelf_id,
            BatchInventory.quantity > 0,
        )
        .limit(1)
    )

    if stock is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot deactivate a shelf containing stock.",
        )

    shelf.is_active = False
    db.commit()

    return {"message": "Shelf deactivated successfully."}
