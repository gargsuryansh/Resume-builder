from sqlalchemy.orm import Session
from config.database import SessionLocal
from models.user import User
from utils.auth import get_password_hash

def create_admin():
    db = SessionLocal()
    try:
        # Check if exists
        user = db.query(User).filter(User.email == "admin@gmail.com").first()
        if user:
            # Update password just in case
            user.hashed_password = get_password_hash("admin123")
            user.role = "admin"
            print("Updated existing admin user.")
        else:
            new_user = User(
                email="admin@gmail.com",
                full_name="System Admin",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(new_user)
            print("Created new admin user.")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
