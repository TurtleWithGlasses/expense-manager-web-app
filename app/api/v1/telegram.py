"""Telegram Bot API — Phase F

Endpoints:
  POST /telegram/webhook         — Telegram pushes updates here
  POST /telegram/generate-code   — Web app calls this to get a link code
  GET  /telegram/status          — Check if current user has Telegram linked
  POST /telegram/unlink          — Unlink from web app settings
"""
from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User

router = APIRouter(prefix="/telegram", tags=["Telegram"])

_CODE_CHARS = string.ascii_uppercase + string.digits
_CODE_LEN   = 6
_CODE_TTL   = 15  # minutes


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_CHARS) for _ in range(_CODE_LEN))


# ── Webhook ───────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram and process them."""
    from app.services.telegram_bot import get_application
    from telegram import Update

    application = get_application()
    if application is None:
        return JSONResponse({"ok": False, "error": "Bot not initialised"}, status_code=503)

    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return JSONResponse({"ok": True})


# ── Link code generation ──────────────────────────────────────────────────────

@router.post("/generate-code")
async def generate_link_code(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Generate a one-time link code for the requesting user."""
    from app.models.telegram_user import TelegramUser, TelegramLinkToken

    # Already linked?
    existing = db.query(TelegramUser).filter(TelegramUser.user_id == user.id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Telegram already linked. Unlink first to generate a new code.",
        )

    # Invalidate any previous unused tokens for this user
    db.query(TelegramLinkToken).filter(
        TelegramLinkToken.user_id == user.id,
        TelegramLinkToken.used == False,
    ).delete()

    # Create new token
    code = _generate_code()
    token = TelegramLinkToken(
        user_id=user.id,
        token=code,
        expires_at=datetime.utcnow() + timedelta(minutes=_CODE_TTL),
    )
    db.add(token)
    db.commit()

    return JSONResponse({
        "code": code,
        "expires_in_minutes": _CODE_TTL,
    })


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def telegram_status(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Return whether the current user has a linked Telegram account."""
    from app.models.telegram_user import TelegramUser

    tg = db.query(TelegramUser).filter(TelegramUser.user_id == user.id).first()
    if tg:
        return JSONResponse({
            "linked": True,
            "telegram_username": tg.telegram_username,
            "linked_at": tg.linked_at.isoformat(),
        })
    return JSONResponse({"linked": False})


# ── Unlink (from web UI) ──────────────────────────────────────────────────────

@router.post("/unlink")
async def unlink_telegram(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    """Unlink the Telegram account associated with the current user."""
    from app.models.telegram_user import TelegramUser

    tg = db.query(TelegramUser).filter(TelegramUser.user_id == user.id).first()
    if not tg:
        raise HTTPException(status_code=404, detail="No linked Telegram account found.")
    db.delete(tg)
    db.commit()
    return JSONResponse({"unlinked": True})
