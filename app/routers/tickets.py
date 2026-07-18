from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.ai import classify_ticket, draft_reply

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=schemas.TicketOut, status_code=201)
def create_ticket(payload: schemas.TicketCreate, db: Session = Depends(get_db)):
    """Create a ticket: it is auto-classified and a reply is drafted."""
    result = classify_ticket(payload.subject, payload.body)
    ticket = models.Ticket(
        customer_email=payload.customer_email,
        subject=payload.subject,
        body=payload.body,
        category=result["category"],
        priority=result["priority"],
        confidence=result["confidence"],
        suggested_reply=draft_reply(payload.subject, payload.body, result["category"]),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[schemas.TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    q = db.query(models.Ticket)
    if category:
        q = q.filter(models.Ticket.category == category)
    if priority:
        q = q.filter(models.Ticket.priority == priority)
    if status:
        q = q.filter(models.Ticket.status == status)
    return q.order_by(models.Ticket.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/stats", response_model=schemas.Stats)
def stats(db: Session = Depends(get_db)):
    def group(col):
        return dict(db.query(col, func.count()).group_by(col).all())

    return schemas.Stats(
        total=db.query(models.Ticket).count(),
        by_category=group(models.Ticket.category),
        by_priority=group(models.Ticket.priority),
        by_status=group(models.Ticket.status),
    )


@router.get("/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=schemas.TicketOut)
def update_status(ticket_id: int, payload: schemas.TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/reclassify", response_model=schemas.TicketOut)
def reclassify(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(models.Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    result = classify_ticket(ticket.subject, ticket.body)
    ticket.category = result["category"]
    ticket.priority = result["priority"]
    ticket.confidence = result["confidence"]
    ticket.suggested_reply = draft_reply(ticket.subject, ticket.body, result["category"])
    db.commit()
    db.refresh(ticket)
    return ticket
