from sqlalchemy.orm import Session
from app.models.category import Category


def list_categories(db: Session, user_id: int):
    return db.query(Category).filter(Category.user_id == user_id).order_by(Category.name).all()


def create_category(db: Session, user_id: int, name: str) -> Category:
    cat = Category(user_id=user_id, name=name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, user_id: int, category_id: int) -> None:
    cat = db.query(Category).filter(
        Category.user_id == user_id, Category.id == category_id
    ).first()
    if cat:
        db.delete(cat)
        db.commit()

def update_category_name(db: Session, user_id: int, category_id: int, new_name: str) -> None:
    cat = db.query(Category).filter(
        Category.user_id == user_id, Category.id == category_id
    ).first()
    if not cat:
        return None
    cat.name = new_name.strip()
    db.commit()
    db.refresh(cat)
    return cat