from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    currency_code: Mapped[str] = mapped_column(String(3), default='USD')
    theme: Mapped[str] = mapped_column(String(10), default='dark')  # 'dark' or 'light'
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationship
    user = relationship("User", back_populates="preferences")