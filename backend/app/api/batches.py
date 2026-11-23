
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Batch, Product
from app.schemas.batch import BatchCreate, BatchOut, BatchUpdate

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.get("/", response_model=list[BatchOut])
def list_batches(
    product_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    statement = select(Batch)

    if product_id is not None:
        statement = statement.where(Batch.product_id == product_id)

    statement = statement.order_by(Batch.expiration_date)

    return db.scalars(statement).all()


@router.post(
    "/",
    response_model=BatchOut,
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    data: BatchCreate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, data.product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found.",
        )

    batch = Batch(**data.model_dump())
    db.add(batch)

    try:
        db.commit()
        db.refresh(batch)
        return batch

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Batch could not be created. A batch with this number "
                "may already exist for this product."
            ),
        )


@router.get("/{batch_id}", response_model=BatchOut)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    batch = db.get(Batch, batch_id)

    if batch is None:
        raise HTTPException(
            status_code=404,
            detail="Batch not found.",
        )

    return batch


@router.put("/{batch_id}", response_model=BatchOut)
def update_batch(
    batch_id: int,
    data: BatchUpdate,
    db: Session = Depends(get_db),
):
    batch = db.get(Batch, batch_id)

    if batch is None:
        raise HTTPException(
            status_code=404,
            detail="Batch not found.",
        )

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(batch, field, value)

    try:
        db.commit()
        db.refresh(batch)
        return batch

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Batch could not be updated. Check that its batch number "
                "is unique for this product and its values are valid."
            ),
        )
