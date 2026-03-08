from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from proekt.backend.auth import decode_access_token
from proekt.backend.database import SessionLocal
from proekt.backend.models import Comment, User

router = APIRouter(prefix="/comments", tags=["comments"])


class CommentCreate(BaseModel):
    folder_id: str
    content: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/folder/{folder_id}")
def get_comments(folder_id: str, token: str = Query(None), db: Session = Depends(get_db)):
    """Отримати коментарі папки з інформацією про можливість видалення"""
    user_id = None
    is_admin = False
    
    # Отримаємо інформацію про поточного користувача
    if token:
        try:
            decoded = decode_access_token(token)
            if decoded and isinstance(decoded, dict):
                user_id = decoded.get("user_id")
                user = db.query(User).filter(User.id == user_id).first()
                is_admin = user is not None and user.role == "admin"
        except:
            pass
    
    comments = db.query(Comment).filter(Comment.folder_id == folder_id).all()
    result = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        result.append(
            {
                "id": c.id,
                "user": user.name if user else "Користувач",
                "content": c.content,
                "created_at": c.created_at.isoformat(),
                "user_id": c.user_id,
                "can_delete": is_admin,  # Адмін може видалити любий коментар
            }
        )
    return result


@router.post("")
def add_comment(
    data: CommentCreate, token: str = Query(None), db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="Необхідна авторизація")

    decoded = decode_access_token(token)
    if not decoded or not isinstance(decoded, dict):
        raise HTTPException(status_code=401, detail="Невалідний токен")

    user_id = decoded.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Невалідний токен")

    comment = Comment(
        folder_id=data.folder_id,
        user_id=user_id,
        content=data.content,
        created_at=datetime.now(timezone.utc),
    )
    db.add(comment)
    db.commit()

    return {"ok": True, "id": comment.id}


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int, token: str = Query(None), db: Session = Depends(get_db)
):
    """Видалити коментар (тільки для адміністраторів)"""
    if not token:
        raise HTTPException(status_code=401, detail="Необхідна авторизація")

    decoded = decode_access_token(token)
    if not decoded or not isinstance(decoded, dict):
        raise HTTPException(status_code=401, detail="Невалідний токен")

    user_id = decoded.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Невалідний токен")

    # Перевіряємо, що користувач - адмін
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Тільки адміністратори можуть видаляти коментарі"
        )

    # Знаходимо і видаляємо коментар
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Коментар не знайдений")

    db.delete(comment)
    db.commit()

    return {"ok": True, "message": "Коментар видалений"}