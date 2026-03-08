from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from proekt.backend.auth import decode_access_token
from proekt.backend.database import SessionLocal
from proekt.backend.models import Rating

router = APIRouter(prefix="/ratings", tags=["ratings"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_user_id(token: str):
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return payload.get("user_id")
    except:
        return None


@router.get("/folder/{folder_id}")
def get_ratings(
    folder_id: str, token: str = Query(None), db: Session = Depends(get_db)
):
    # Get average and count
    result = (
        db.query(func.avg(Rating.rating), func.count(Rating.id))
        .filter(Rating.folder_id == folder_id)
        .first()
    )
    average = float(result[0]) if result[0] else 0.0
    count = result[1] or 0

    user_rating = 0
    user_id = _get_user_id(token)
    if user_id:
        user_rate = (
            db.query(Rating.rating)
            .filter(Rating.folder_id == folder_id, Rating.user_id == user_id)
            .first()
        )
        if user_rate:
            user_rating = user_rate[0]

    return {"average": average, "count": count, "userRating": user_rating}


class RatingRequest(BaseModel):
    folder_id: str
    rating: int


@router.post("")
def submit_rating(
    rating_req: RatingRequest, token: str = Query(...), db: Session = Depends(get_db)
):
    user_id = _get_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if already rated
    existing = (
        db.query(Rating)
        .filter(Rating.folder_id == rating_req.folder_id, Rating.user_id == user_id)
        .first()
    )
    if existing:
        # Update
        existing.rating = rating_req.rating
    else:
        # Create
        new_rating = Rating(
            folder_id=rating_req.folder_id, user_id=user_id, rating=rating_req.rating
        )
        db.add(new_rating)

    db.commit()

    # Recalculate
    result = (
        db.query(func.avg(Rating.rating), func.count(Rating.id))
        .filter(Rating.folder_id == rating_req.folder_id)
        .first()
    )
    average = float(result[0]) if result[0] else 0.0
    count = result[1] or 0

    return {"average": average, "count": count}
