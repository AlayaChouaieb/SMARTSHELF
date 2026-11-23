from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Product
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductOut])
def list_products(
    search: str | None = Query(default=None),
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    statement = select(Product)

    if active_only:
        statement = statement.where(Product.is_active.is_(True))

    if search:
        statement = statement.where(
            Product.name.ilike(f"%{search}%")
            | Product.barcode.ilike(f"%{search}%")
            | Product.sku.ilike(f"%{search}%")
        )

    statement = statement.order_by(Product.name)

    return db.scalars(statement).all()


@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
):
    product_data = data.model_dump()

    product = Product(**product_data)
    db.add(product)

    try:
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Product could not be created. Check that its barcode "
                "and SKU are unique, its category and supplier exist, "
                "and max_stock is not lower than min_stock."
            ),
        )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Product could not be updated. Check unique barcode/SKU, "
                "category and supplier references, and stock constraints."
            ),
        )


@router.delete("/{product_id}")
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")

    product.is_active = False
    db.commit()

    return {
        "message": "Product deactivated successfully.",
        "product_id": product.id,
    }