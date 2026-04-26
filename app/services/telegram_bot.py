"""
Telegram Bot Service — Phase F (F-1 – F-3) + Phase G-4 (photo scanning)

Commands:
  /start   — welcome + help
  /link    — link Telegram to web account
  /unlink  — disconnect
  /add     — guided income/expense entry (multi-step conversation)
  /undo    — delete the last bot-created entry (within 5 min)
  /balance — this month income vs expenses
  /today   — today's entries
  /week    — this week's spending by category
  /history — last N entries
  /cancel  — abort current conversation

Photo:
  Send any photo → AI scans it as a receipt and asks to confirm saving
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Conversation states
TYPE_SELECT, CATEGORY_SELECT, AMOUNT_ENTER = range(3)

# Currency symbols for quick formatting
_SYMBOLS: dict[str, str] = {"TRY": "₺", "USD": "$", "EUR": "€", "GBP": "£"}


# ── DB helpers ────────────────────────────────────────────────────────────────

def _db():
    return SessionLocal()


def _get_tg_user(db, telegram_user_id: int):
    from app.models.telegram_user import TelegramUser
    return db.query(TelegramUser).filter(
        TelegramUser.telegram_user_id == telegram_user_id
    ).first()


def _get_currency(db, user_id: int) -> str:
    from app.services.user_preferences import user_preferences_service
    return user_preferences_service.get_user_currency(db, user_id)


def _sym(currency: str) -> str:
    return _SYMBOLS.get(currency, currency + " ")


def _parse_amount(text: str) -> Optional[Decimal]:
    """Parse user-entered amount; handles 1414.95, 1.414,95, 1,414.95."""
    import re
    s = text.strip().replace(" ", "")
    if re.match(r'^\d{1,3}(?:\.\d{3})*,\d{2}$', s):
        s = s.replace('.', '').replace(',', '.')
    elif re.match(r'^\d{1,3}(?:,\d{3})*\.\d{2}$', s):
        s = s.replace(',', '')
    else:
        s = s.replace(',', '.')
    try:
        val = Decimal(s)
        return val if val > 0 else None
    except InvalidOperation:
        return None


def _not_linked_msg() -> str:
    return (
        "🔗 Account not linked.\n\n"
        "1. Open the web app → *Settings*\n"
        "2. Click *Generate Link Code*\n"
        "3. Send: `/link YOUR_CODE`"
    )


# ── /start ────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if tg_user:
            text = (
                "👋 Welcome back to *Budget Pulse*!\n\n"
                "📷 *Send a photo* of a receipt to scan it instantly\n\n"
                "/add — Log income or expense manually\n"
                "/balance — This month's summary\n"
                "/today — Today's entries\n"
                "/week — This week's spending\n"
                "/history — Last 5 entries\n"
                "/help — All commands"
            )
        else:
            from app.core.config import settings as app_settings
            settings_url = f"{app_settings.BASE_URL}/settings"
            text = (
                "👋 Welcome to *Budget Pulse*!\n\n"
                "To get started, link your web account:\n\n"
                f"1️⃣ Open: {settings_url}\n"
                "2️⃣ Scroll to *Telegram Bot* → tap *Generate Link Code*\n"
                "3️⃣ Send me: `/link YOUR_CODE`\n\n"
                "Once linked you can log expenses, check your balance, and more — all from Telegram."
            )
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        db.close()


# ── /help ─────────────────────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Budget Pulse — Commands*\n\n"
        "📷 *Send a photo* of a receipt → AI scans it automatically\n\n"
        "/add — Log a new income or expense\n"
        "/undo — Remove the last entry you added (within 5 min)\n"
        "/balance — This month's income vs expenses\n"
        "/today — All entries from today\n"
        "/week — This week's spending by category\n"
        "/history [N] — Last N entries (default 5)\n"
        "/link <code> — Connect your Budget Pulse account\n"
        "/unlink — Disconnect your account\n"
        "/cancel — Cancel current action",
        parse_mode="Markdown",
    )


# ── /link ─────────────────────────────────────────────────────────────────────

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Please provide your link code:\n`/link YOUR_CODE`\n\n"
            "Get the code from *Settings → Generate Link Code* in the web app.",
            parse_mode="Markdown",
        )
        return

    code = context.args[0].strip().upper()
    tg_id = update.effective_user.id
    tg_username = update.effective_user.username

    db = _db()
    try:
        from app.models.telegram_user import TelegramUser, TelegramLinkToken

        # Already linked?
        if _get_tg_user(db, tg_id):
            await update.message.reply_text(
                "✅ Your account is already linked!\nUse /unlink first if you want to reconnect."
            )
            return

        token = db.query(TelegramLinkToken).filter(
            TelegramLinkToken.token == code,
            TelegramLinkToken.used == False,
            TelegramLinkToken.expires_at > datetime.utcnow(),
        ).first()

        if not token:
            await update.message.reply_text(
                "❌ Invalid or expired code.\n"
                "Generate a new one in *Settings → Generate Link Code*.",
                parse_mode="Markdown",
            )
            return

        db.add(TelegramUser(
            user_id=token.user_id,
            telegram_user_id=tg_id,
            telegram_username=tg_username,
        ))
        token.used = True
        db.commit()

        await update.message.reply_text(
            "✅ *Account linked!*\n\n"
            "You can now use:\n"
            "/add — Log a new entry\n"
            "/balance — Check your balance\n"
            "/help — All commands",
            parse_mode="Markdown",
        )
    finally:
        db.close()


# ── /unlink ───────────────────────────────────────────────────────────────────

async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text("Your account is not currently linked.")
            return
        db.delete(tg_user)
        db.commit()
        await update.message.reply_text("✅ Account unlinked. Use /link to reconnect.")
    finally:
        db.close()


# ── /add conversation ─────────────────────────────────────────────────────────

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db = _db()
    try:
        if not _get_tg_user(db, update.effective_user.id):
            await update.message.reply_text(_not_linked_msg(), parse_mode="Markdown")
            return ConversationHandler.END
    finally:
        db.close()

    keyboard = [[
        InlineKeyboardButton("📈 Income",  callback_data="type_income"),
        InlineKeyboardButton("📉 Expense", callback_data="type_expense"),
    ]]
    await update.message.reply_text(
        "💳 *New Entry*\n\nWhat type?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return TYPE_SELECT


async def type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    entry_type = query.data.replace("type_", "")   # "income" | "expense"
    context.user_data["entry_type"] = entry_type

    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await query.edit_message_text("Session expired. Use /add to start over.")
            return ConversationHandler.END

        from app.models.category import Category
        cats = (
            db.query(Category)
            .filter(Category.user_id == tg_user.user_id)
            .order_by(Category.name)
            .all()
        )

        # 2 per row
        buttons: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []
        for cat in cats:
            row.append(InlineKeyboardButton(cat.name, callback_data=f"cat_{cat.id}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("— No category —", callback_data="cat_0")])

        emoji = "📈" if entry_type == "income" else "📉"
        label = "Income" if entry_type == "income" else "Expense"
        await query.edit_message_text(
            f"{emoji} *{label}*\n\nSelect a category:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )
        return CATEGORY_SELECT
    finally:
        db.close()


async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    cat_raw = query.data.replace("cat_", "")
    cat_id = int(cat_raw) if cat_raw != "0" else None
    context.user_data["category_id"] = cat_id

    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await query.edit_message_text("Session expired. Use /add to start over.")
            return ConversationHandler.END

        cat_name = "No category"
        if cat_id:
            from app.models.category import Category
            cat = db.query(Category).filter(Category.id == cat_id).first()
            if cat:
                cat_name = cat.name
        context.user_data["category_name"] = cat_name

        currency = _get_currency(db, tg_user.user_id)
        context.user_data["currency"] = currency
        s = _sym(currency)

        await query.edit_message_text(
            f"💰 Enter amount ({s}{currency}):\n\n_Send /cancel to abort_",
            parse_mode="Markdown",
        )
        return AMOUNT_ENTER
    finally:
        db.close()


async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = _parse_amount(update.message.text)
    if amount is None:
        await update.message.reply_text(
            "❌ Couldn't parse that. Enter a number like `150` or `1414.95`.",
            parse_mode="Markdown",
        )
        return AMOUNT_ENTER

    entry_type    = context.user_data.get("entry_type", "expense")
    category_id   = context.user_data.get("category_id")
    category_name = context.user_data.get("category_name", "No category")
    currency      = context.user_data.get("currency", "USD")

    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text("Session expired. Use /add to start over.")
            return ConversationHandler.END

        from app.services import entries as entries_service
        entry = entries_service.create_entry(
            db,
            user_id=tg_user.user_id,
            type=entry_type,
            amount=float(amount),
            date=date.today(),
            category_id=category_id,
            note="via Telegram",
            currency_code=currency,
        )

        # Store for /undo
        tg_user.last_entry_id = entry.id
        tg_user.last_entry_at = datetime.utcnow()
        db.commit()

        # Award XP (best-effort)
        try:
            from app.services.gamification import LevelService
            LevelService(db).award_entry_xp(tg_user.user_id)
        except Exception:
            pass

        s = _sym(currency)
        emoji = "📈" if entry_type == "income" else "📉"
        label = "Income" if entry_type == "income" else "Expense"

        await update.message.reply_text(
            f"✅ *Saved!*\n\n"
            f"{emoji} {label}\n"
            f"💰 {s}{float(amount):,.2f} {currency}\n"
            f"📂 {category_name}\n"
            f"📅 {date.today().strftime('%d %b %Y')}\n\n"
            f"_Use /undo to remove it (within 5 min)_",
            parse_mode="Markdown",
        )
        context.user_data.clear()
        return ConversationHandler.END
    finally:
        db.close()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# ── /undo ─────────────────────────────────────────────────────────────────────

async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user or not tg_user.last_entry_id:
            await update.message.reply_text("Nothing to undo.")
            return

        # 5-minute window
        if tg_user.last_entry_at:
            age = (datetime.utcnow() - tg_user.last_entry_at).total_seconds()
            if age > 300:
                await update.message.reply_text(
                    "⏱ Too late — entries can only be undone within 5 minutes of creation."
                )
                return

        from app.models.entry import Entry
        entry = db.query(Entry).filter(
            Entry.id == tg_user.last_entry_id,
            Entry.user_id == tg_user.user_id,
        ).first()

        if not entry:
            await update.message.reply_text("Entry not found (already deleted?).")
            tg_user.last_entry_id = None
            db.commit()
            return

        db.delete(entry)
        tg_user.last_entry_id = None
        tg_user.last_entry_at = None
        db.commit()
        await update.message.reply_text("✅ Entry deleted.")
    finally:
        db.close()


# ── /balance ──────────────────────────────────────────────────────────────────

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text(_not_linked_msg(), parse_mode="Markdown")
            return

        from app.models.entry import Entry
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()

        entries = (
            db.query(Entry)
            .filter(Entry.user_id == tg_user.user_id, Entry.date >= month_start)
            .all()
        )

        income   = sum(float(e.amount) for e in entries if e.type == "income")
        expenses = sum(float(e.amount) for e in entries if e.type == "expense")
        net      = income - expenses

        currency = _get_currency(db, tg_user.user_id)
        s = _sym(currency)

        cat_totals: dict[str, float] = {}
        for e in entries:
            if e.type == "expense":
                name = e.category.name if e.category else "Uncategorized"
                cat_totals[name] = cat_totals.get(name, 0) + float(e.amount)
        top = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:3]

        top_text = ""
        if top:
            top_text = "\n\n*Top categories:*\n" + "\n".join(
                f"  • {name}: {s}{amt:,.2f}" for name, amt in top
            )

        sign = "+" if net >= 0 else "−"
        net_display = f"{sign}{s}{abs(net):,.2f}"

        await update.message.reply_text(
            f"📊 *{now.strftime('%B %Y')}*\n\n"
            f"📈 Income:    {s}{income:,.2f}\n"
            f"📉 Expenses:  {s}{expenses:,.2f}\n"
            f"💰 Net:       {net_display}"
            + top_text,
            parse_mode="Markdown",
        )
    finally:
        db.close()


# ── /today ────────────────────────────────────────────────────────────────────

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text(_not_linked_msg(), parse_mode="Markdown")
            return

        from app.models.entry import Entry
        today = date.today()
        entries = (
            db.query(Entry)
            .filter(Entry.user_id == tg_user.user_id, Entry.date == today)
            .order_by(Entry.id.desc())
            .all()
        )

        if not entries:
            await update.message.reply_text(
                f"No entries for today ({today.strftime('%d %b %Y')}).\n/add to log one."
            )
            return

        currency = _get_currency(db, tg_user.user_id)
        s = _sym(currency)

        lines = [f"📅 *{today.strftime('%d %b %Y')}*\n"]
        for e in entries:
            emoji = "📈" if e.type == "income" else "📉"
            cat   = e.category.name if e.category else "–"
            lines.append(f"{emoji} {s}{float(e.amount):,.2f}  _{cat}_")

        spent  = sum(float(e.amount) for e in entries if e.type == "expense")
        earned = sum(float(e.amount) for e in entries if e.type == "income")
        if len(entries) > 1:
            lines.append(f"\n📉 Spent today: {s}{spent:,.2f}")
            if earned:
                lines.append(f"📈 Earned today: {s}{earned:,.2f}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


# ── /week ─────────────────────────────────────────────────────────────────────

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text(_not_linked_msg(), parse_mode="Markdown")
            return

        from app.models.entry import Entry
        today      = date.today()
        week_start = today - timedelta(days=today.weekday())

        entries = (
            db.query(Entry)
            .filter(
                Entry.user_id == tg_user.user_id,
                Entry.date >= week_start,
                Entry.type == "expense",
            )
            .all()
        )

        if not entries:
            await update.message.reply_text(
                f"No expenses this week "
                f"({week_start.strftime('%d %b')} – {today.strftime('%d %b')})."
            )
            return

        currency = _get_currency(db, tg_user.user_id)
        s = _sym(currency)

        cat_totals: dict[str, float] = {}
        for e in entries:
            name = e.category.name if e.category else "Uncategorized"
            cat_totals[name] = cat_totals.get(name, 0) + float(e.amount)

        total = sum(cat_totals.values())
        lines = [
            f"📅 *This Week*  "
            f"({week_start.strftime('%d %b')} – {today.strftime('%d %b')})\n"
        ]
        for name, amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
            pct = amt / total * 100
            lines.append(f"  • {name}: {s}{amt:,.2f} ({pct:.0f}%)")
        lines.append(f"\n📉 *Total: {s}{total:,.2f}*")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


# ── /history ──────────────────────────────────────────────────────────────────

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text(_not_linked_msg(), parse_mode="Markdown")
            return

        count = 5
        if context.args:
            try:
                count = max(1, min(int(context.args[0]), 20))
            except ValueError:
                pass

        from app.models.entry import Entry
        entries = (
            db.query(Entry)
            .filter(Entry.user_id == tg_user.user_id)
            .order_by(Entry.date.desc(), Entry.id.desc())
            .limit(count)
            .all()
        )

        if not entries:
            await update.message.reply_text("No entries yet.\n/add to log your first one.")
            return

        currency = _get_currency(db, tg_user.user_id)
        s = _sym(currency)

        lines = [f"🗒 *Last {len(entries)} entries*\n"]
        for e in entries:
            emoji = "📈" if e.type == "income" else "📉"
            cat   = e.category.name if e.category else "–"
            lines.append(
                f"{emoji} {e.date.strftime('%d %b')}  {s}{float(e.amount):,.2f}  _{cat}_"
            )

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


# ── G-4: Photo receipt scanning ──────────────────────────────────────────────

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User sent a photo — download it, run AI scan, ask for confirmation."""
    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await update.message.reply_text(_not_linked_msg(), parse_mode="Markdown")
            return

        from app.core.config import settings
        if not settings.ANTHROPIC_API_KEY:
            await update.message.reply_text(
                "📷 Receipt scanning via photo requires AI Vision, which is not enabled on this server.\n"
                "Use the web app to scan receipts instead."
            )
            return

        processing_msg = await update.message.reply_text(
            "📷 *Scanning receipt…*\n_AI Vision is reading your photo_",
            parse_mode="Markdown",
        )

        # Download largest available photo size
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = bytes(await photo_file.download_as_bytearray())

        from app.services.ai_receipt_service import scan_with_ai
        try:
            result = scan_with_ai(image_bytes, settings.ANTHROPIC_API_KEY)
        except Exception as exc:
            logger.warning("AI scan failed in bot photo handler: %s", exc)
            await processing_msg.edit_text(
                "❌ Could not read the receipt. Try a clearer, well-lit photo or use /add to log it manually."
            )
            return

        amount = result.get("total_amount")
        if not amount:
            await processing_msg.edit_text(
                "❌ Could not find a total amount in the receipt.\n"
                "Try a clearer photo, or use /add to log it manually."
            )
            return

        merchant = result.get("merchant") or "Unknown merchant"
        date_str = result.get("date") or date.today().isoformat()
        currency = _get_currency(db, tg_user.user_id)
        s        = _sym(currency)

        # Suggest category from merchant name
        from app.models.category import Category
        from app.services.category_suggester import suggest_category
        cats = db.query(Category).filter(Category.user_id == tg_user.user_id).order_by(Category.name).all()
        suggestion = suggest_category(merchant, "", cats, db=db, user_id=tg_user.user_id)
        cat_id   = suggestion["category_id"]   if suggestion else None
        cat_name = suggestion["category_name"] if suggestion else "No category"

        # Store pending receipt for the confirm callback
        context.user_data["pending_receipt"] = {
            "merchant":      merchant,
            "amount":        amount,
            "date":          date_str,
            "currency":      currency,
            "category_id":   cat_id,
            "category_name": cat_name,
        }

        conf      = result.get("confidence", "medium")
        conf_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(conf, "🟡")

        try:
            date_display = datetime.strptime(date_str, "%Y-%m-%d").date().strftime("%d %b %Y")
        except ValueError:
            date_display = date_str

        text = (
            f"📄 *Receipt Scanned* {conf_icon}\n\n"
            f"🏪 *Merchant:* {merchant}\n"
            f"💰 *Amount:*   {s}{float(amount):,.2f} {currency}\n"
            f"📅 *Date:*     {date_display}\n"
            f"📂 *Category:* {cat_name}\n\n"
            f"Save this as an expense entry?"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Save", callback_data="receipt_save"),
            InlineKeyboardButton("❌ Discard", callback_data="receipt_cancel"),
        ]])
        await processing_msg.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

    finally:
        db.close()


async def receipt_save_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Save the pending scanned receipt as an expense entry."""
    query = update.callback_query
    await query.answer()

    pending = context.user_data.get("pending_receipt")
    if not pending:
        await query.edit_message_text("⏱ Session expired. Send the photo again.")
        return

    db = _db()
    try:
        tg_user = _get_tg_user(db, update.effective_user.id)
        if not tg_user:
            await query.edit_message_text("Account not linked. Use /link.")
            return

        from app.services import entries as entries_service
        from datetime import date as date_type
        try:
            entry_date = date_type.fromisoformat(pending["date"])
        except (ValueError, KeyError):
            entry_date = date_type.today()

        entry = entries_service.create_entry(
            db,
            user_id=tg_user.user_id,
            type="expense",
            amount=float(pending["amount"]),
            date=entry_date,
            category_id=pending.get("category_id"),
            note=pending.get("merchant", "Receipt")[:255],
            currency_code=pending.get("currency", "USD"),
        )

        tg_user.last_entry_id = entry.id
        tg_user.last_entry_at = datetime.utcnow()
        db.commit()

        try:
            from app.services.gamification import LevelService
            LevelService(db).award_entry_xp(tg_user.user_id)
        except Exception:
            pass

        s = _sym(pending.get("currency", "USD"))
        await query.edit_message_text(
            f"✅ *Saved!*\n\n"
            f"📉 Expense\n"
            f"💰 {s}{float(pending['amount']):,.2f}\n"
            f"📂 {pending.get('category_name', '–')}\n"
            f"📅 {entry_date.strftime('%d %b %Y')}\n\n"
            f"_Use /undo to remove it (within 5 min)_",
            parse_mode="Markdown",
        )
        context.user_data.pop("pending_receipt", None)
    finally:
        db.close()


async def receipt_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Discard the pending scanned receipt without saving."""
    query = update.callback_query
    await query.answer()
    context.user_data.pop("pending_receipt", None)
    await query.edit_message_text("❌ Receipt discarded.")


# ── Application factory ───────────────────────────────────────────────────────

_application: Application | None = None


def get_application() -> Application | None:
    return _application


_BOT_COMMANDS = [
    ("add",     "Log a new income or expense"),
    ("balance", "This month's income vs expenses"),
    ("today",   "All entries from today"),
    ("week",    "This week's spending by category"),
    ("history", "Last 5 entries (use /history 10 for more)"),
    ("undo",    "Remove the last entry you added (within 5 min)"),
    ("link",    "Connect your Budget Pulse account"),
    ("unlink",  "Disconnect your account"),
    ("help",    "Show all available commands"),
]


async def setup_bot(token: str, webhook_url: str | None = None) -> None:
    """Initialise the bot, register commands, and optionally set the webhook."""
    global _application
    _application = create_application(token)
    await _application.initialize()

    # Register commands so Telegram shows autocomplete for all users
    from telegram import BotCommand
    await _application.bot.set_my_commands(
        [BotCommand(cmd, desc) for cmd, desc in _BOT_COMMANDS]
    )
    logger.info("Telegram bot commands registered (%d commands)", len(_BOT_COMMANDS))

    if webhook_url:
        await _application.bot.set_webhook(webhook_url)
        logger.info("Telegram webhook registered: %s", webhook_url)
    else:
        logger.info("Telegram bot initialised (no webhook URL — dev/local mode)")


async def teardown_bot() -> None:
    global _application
    if _application:
        await _application.shutdown()
        _application = None


def create_application(token: str) -> Application:
    """Build and return the configured PTB Application."""
    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_command)],
        states={
            TYPE_SELECT:     [CallbackQueryHandler(type_chosen,     pattern=r"^type_")],
            CATEGORY_SELECT: [CallbackQueryHandler(category_chosen, pattern=r"^cat_")],
            AMOUNT_ENTER:    [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(CommandHandler("start",   start))
    application.add_handler(CommandHandler("help",    help_command))
    application.add_handler(CommandHandler("link",    link_command))
    application.add_handler(CommandHandler("unlink",  unlink_command))
    application.add_handler(CommandHandler("undo",    undo_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("today",   today_command))
    application.add_handler(CommandHandler("week",    week_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(conv_handler)

    # G-4: photo receipt scanning (must be after conv_handler)
    application.add_handler(MessageHandler(filters.PHOTO, photo_received))
    application.add_handler(CallbackQueryHandler(receipt_save_callback,   pattern=r"^receipt_save$"))
    application.add_handler(CallbackQueryHandler(receipt_cancel_callback, pattern=r"^receipt_cancel$"))

    return application
