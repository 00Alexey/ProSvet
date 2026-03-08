from proekt.backend.database import SessionLocal
from proekt.backend.models import User

db = SessionLocal()
user = db.query(User).filter(User.email == "prosvet333stellarastra@gmail.com").first()
if user:
    user.role = "admin"
    db.commit()
else:
    print("User not found")

db.close()
