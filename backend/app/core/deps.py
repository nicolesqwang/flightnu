"""Single-user mode: no auth yet, every request operates as one implicit user."""

from sqlalchemy.orm import Session

from app.models.models import User

DEFAULT_USER_EMAIL = "demo@flightnu.app"


def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
    if user is None:
        user = User(email=DEFAULT_USER_EMAIL)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
