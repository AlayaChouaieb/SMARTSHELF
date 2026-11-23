
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Alert
from app.schemas.alert import AlertOut
from app.services.alert_service import refresh_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/refresh")
def refresh_alerts_endpoint(
    db: Session = Depends(get_db),
):
    return refresh_alerts(db)


@router.get("/", response_model=list[AlertOut])
def list_alerts(
    alert_type: str | None = Query(default=None),
    unread_only: bool = Query(default=False),
    unresolved_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    statement = select(Alert)

    if alert_type is not None:
        statement = statement.where(Alert.alert_type == alert_type.upper())

    if unread_only:
        statement = statement.where(Alert.is_read.is_(False))

    if unresolved_only:
        statement = statement.where(Alert.is_resolved.is_(False))

    statement = statement.order_by(Alert.created_at.desc())

    return db.scalars(statement).all()


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.get(Alert, alert_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found.")

    return alert


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.get(Alert, alert_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.is_read = True
    db.commit()
    db.refresh(alert)

    return alert


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.get(Alert, alert_id)

    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found.")

    alert.is_resolved = True

    from datetime import datetime, timezone
    alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(alert)

    return alert
