from proekt.backend.database import SessionLocal
from proekt.backend.models import User

if __name__ == '__main__':
    db = SessionLocal()
    try:
        users = db.query(User).all()
        changed = 0
        for u in users:
            if u.email and u.email.strip() != u.email:
                u.email = u.email.strip().lower()
                changed += 1
            elif u.email and u.email.lower() != u.email:
                u.email = u.email.lower()
                changed += 1
        if changed:
            db.commit()
        print(f"Normalized {changed} users")
    finally:
        db.close()
