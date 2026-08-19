from sqlalchemy.orm import Session
from backend.app.core.security import get_password_hash
from backend.app.models.entities import User, Base
from backend.app.db.session import engine

def init_db(db: Session) -> None:
    """
    Initializes database schema and ensures default admin and editor users exist.
    """
    Base.metadata.create_all(bind=engine)

    # Check if admin user exists
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@peblo.tv",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)

    # Check if editor user exists
    editor_user = db.query(User).filter(User.username == "editor").first()
    if not editor_user:
        editor_user = User(
            username="editor",
            email="editor@peblo.tv",
            hashed_password=get_password_hash("editor123"),
            role="editor",
            is_active=True
        )
        db.add(editor_user)

    db.commit()

if __name__ == "__main__":
    from backend.app.db.session import SessionLocal
    with SessionLocal() as db_session:
        init_db(db_session)
        print("Database schema and default users initialized successfully.")
