"""
Generate realistic PWA screenshots for BudgetPulse manifest.json.

Run:  python scripts/generate_pwa_screenshots.py
Output: static/screenshots/desktop-dashboard.png  (1280x720)
        static/screenshots/mobile-entries.png      (750x1334)
"""
from PIL import Image, ImageDraw, ImageFont
import os, math

# ── colour palette (dark theme matching the app) ──────────────────────────────
BG        = (15, 20, 35)       # --bg
SURFACE   = (22, 29, 49)       # --surface
SURFACE2  = (28, 37, 62)       # card bg
BORDER    = (45, 55, 80)
PRIMARY   = (59, 130, 246)     # --primary (blue)
SUCCESS   = (16, 185, 129)     # --success (green)
DANGER    = (239, 68, 68)      # --danger  (red)
WARNING   = (245, 158, 11)     # --warning (amber)
TEXT      = (226, 232, 240)    # --text
MUTED     = (100, 116, 139)    # --text-muted
WHITE     = (255, 255, 255)
PURPLE    = (139, 92, 246)

# ── font helpers ──────────────────────────────────────────────────────────────
def _font(size):
    for name in ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()

def _font_regular(size):
    for name in ["arial.ttf", "DejaVuSans.ttf", "Arial.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()

# ── drawing helpers ───────────────────────────────────────────────────────────
def rrect(draw, xy, radius, fill, outline=None, outline_width=1):
    """Rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill,
                            outline=outline, width=outline_width)

def text_center(draw, text, x, y, w, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) // 2, y), text, font=font, fill=fill)

def progress_bar(draw, x, y, w, h, pct, color=PRIMARY, bg=BORDER, radius=4):
    rrect(draw, (x, y, x + w, y + h), radius, bg)
    if pct > 0:
        rrect(draw, (x, y, x + int(w * pct), y + h), radius, color)

def dot(draw, x, y, r, color):
    draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

# ── stat card ─────────────────────────────────────────────────────────────────
def stat_card(draw, x, y, w, h, label, value, sub=None, accent=PRIMARY):
    rrect(draw, (x, y, x + w, y + h), 12, SURFACE2, BORDER, 1)
    # accent strip on left
    draw.rectangle((x, y + 12, x + 3, y + h - 12), fill=accent)
    # value
    vf = _font(28)
    draw.text((x + 16, y + 14), value, font=vf, fill=WHITE)
    # label
    lf = _font_regular(14)
    draw.text((x + 16, y + h - 28), label, font=lf, fill=MUTED)
    if sub:
        sf = _font_regular(12)
        bbox = draw.textbbox((0, 0), sub, font=sf)
        sw = bbox[2] - bbox[0]
        draw.text((x + w - sw - 10, y + 16), sub, font=sf, fill=SUCCESS)


# ════════════════════════════════════════════════════════════════════════════════
# DESKTOP DASHBOARD  1280 × 720
# ════════════════════════════════════════════════════════════════════════════════
def make_desktop():
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    SIDEBAR_W = 220
    TOPBAR_H  = 56

    # ── sidebar ──────────────────────────────────────────────────────────────
    d.rectangle((0, 0, SIDEBAR_W, H), fill=SURFACE)
    d.rectangle((SIDEBAR_W, 0, SIDEBAR_W + 1, H), fill=BORDER)

    # logo
    bf = _font(18)
    d.text((20, 16), "⚡ BudgetPulse", font=bf, fill=PRIMARY)

    nav_items = [
        ("📊", "Dashboard",    True),
        ("💰", "Entries",      False),
        ("📁", "Categories",   False),
        ("📈", "Reports",      False),
        ("🎯", "Goals",        False),
        ("🏆", "Achievements", False),
        ("👥", "Split Expenses",False),
        ("⚡", "Challenges",   False),
        ("🔔", "Bills",        False),
    ]
    y = 80
    nf = _font_regular(14)
    for icon, label, active in nav_items:
        if active:
            rrect(d, (8, y - 4, SIDEBAR_W - 8, y + 30), 8, PRIMARY + (30,))
            d.text((16, y + 2), f"{icon}  {label}", font=nf, fill=PRIMARY)
        else:
            d.text((16, y + 2), f"{icon}  {label}", font=nf, fill=MUTED)
        y += 40

    # settings at bottom
    sf = _font_regular(13)
    d.text((16, H - 80), "⚙️  Settings", font=sf, fill=MUTED)
    d.text((16, H - 48), "👤  Profile",  font=sf, fill=MUTED)

    # ── topbar ────────────────────────────────────────────────────────────────
    d.rectangle((SIDEBAR_W, 0, W, TOPBAR_H), fill=SURFACE)
    d.rectangle((SIDEBAR_W, TOPBAR_H, W, TOPBAR_H + 1), fill=BORDER)
    tf = _font(16)
    d.text((SIDEBAR_W + 20, 16), "Dashboard", font=tf, fill=TEXT)
    # date chip
    df = _font_regular(12)
    chip_x = W - 200
    rrect(d, (chip_x, 14, W - 16, TOPBAR_H - 14), 8, SURFACE2, BORDER)
    d.text((chip_x + 10, 18), "March 2026", font=df, fill=MUTED)

    # ── content area ─────────────────────────────────────────────────────────
    cx = SIDEBAR_W + 20
    cy = TOPBAR_H + 20
    CW = W - SIDEBAR_W - 40

    # top stat cards row
    card_w = (CW - 30) // 4
    stats = [
        ("Total Income",   "$4,820",  "+12%",  SUCCESS),
        ("Total Expenses", "$3,147",  "-5%",   DANGER),
        ("Net Savings",    "$1,673",  "+28%",  SUCCESS),
        ("Savings Rate",   "34.7%",   "",      PRIMARY),
    ]
    for i, (lbl, val, sub, acc) in enumerate(stats):
        stat_card(d, cx + i * (card_w + 10), cy, card_w, 88, lbl, val, sub or None, acc)

    cy += 104

    # ── spending trend chart (fake line chart) ────────────────────────────────
    chart_w = int(CW * 0.62)
    chart_h = 200
    rrect(d, (cx, cy, cx + chart_w, cy + chart_h), 12, SURFACE2, BORDER)
    cf = _font(13)
    d.text((cx + 16, cy + 12), "Spending Trend", font=cf, fill=TEXT)

    # axes
    ax, ay = cx + 20, cy + 40
    aw, ah = chart_w - 40, chart_h - 60
    d.rectangle((ax, ay, ax + aw, ay + ah), fill=SURFACE)

    # grid lines
    for i in range(5):
        gy = ay + i * (ah // 4)
        d.line((ax, gy, ax + aw, gy), fill=BORDER, width=1)

    # expense line (red)
    expense_pts = [120, 180, 145, 200, 160, 130, 175, 155, 140, 190, 165, 148]
    max_v = max(expense_pts)
    pts_e = []
    for i, v in enumerate(expense_pts):
        px = ax + int(i * aw / (len(expense_pts) - 1))
        py = ay + ah - int(v / max_v * ah * 0.85)
        pts_e.append((px, py))
    for i in range(len(pts_e) - 1):
        d.line([pts_e[i], pts_e[i+1]], fill=DANGER, width=2)
    for p in pts_e:
        dot(d, p[0], p[1], 3, DANGER)

    # income line (green)
    income_pts = [200, 200, 200, 350, 200, 200, 200, 200, 200, 200, 420, 200]
    pts_i = []
    for i, v in enumerate(income_pts):
        px = ax + int(i * aw / (len(income_pts) - 1))
        py = ay + ah - int(v / max_v * ah * 0.85)
        pts_i.append((px, py))
    for i in range(len(pts_i) - 1):
        d.line([pts_i[i], pts_i[i+1]], fill=SUCCESS, width=2)

    # legend
    lf = _font_regular(11)
    dot(d, cx + 16, cy + chart_h - 14, 5, SUCCESS)
    d.text((cx + 26, cy + chart_h - 20), "Income", font=lf, fill=MUTED)
    dot(d, cx + 86, cy + chart_h - 14, 5, DANGER)
    d.text((cx + 96, cy + chart_h - 20), "Expenses", font=lf, fill=MUTED)

    # ── category doughnut (simplified) ───────────────────────────────────────
    pie_x = cx + chart_w + 20
    pie_w = CW - chart_w - 30
    pie_h = chart_h
    rrect(d, (pie_x, cy, pie_x + pie_w, cy + pie_h), 12, SURFACE2, BORDER)
    d.text((pie_x + 12, cy + 12), "By Category", font=cf, fill=TEXT)

    cats = [
        ("Food",    0.32, DANGER),
        ("Housing", 0.25, PRIMARY),
        ("Transp.",  0.18, WARNING),
        ("Shopping",0.15, PURPLE),
        ("Other",   0.10, MUTED),
    ]
    # Draw horizontal bars instead of a pie
    bar_y = cy + 38
    for lbl, pct, col in cats:
        bw = int((pie_w - 24) * pct)
        rrect(d, (pie_x + 12, bar_y, pie_x + 12 + bw, bar_y + 18), 4, col)
        d.text((pie_x + 14, bar_y + 2), f"{lbl}  {int(pct*100)}%", font=_font_regular(11), fill=WHITE)
        bar_y += 28

    cy += chart_h + 16

    # ── recent entries table ──────────────────────────────────────────────────
    table_h = H - cy - 20
    rrect(d, (cx, cy, cx + CW, cy + table_h), 12, SURFACE2, BORDER)
    d.text((cx + 16, cy + 12), "Recent Entries", font=cf, fill=TEXT)

    entries = [
        ("Today",    "Coffee & Snacks",     "Food",     "-$8.50",  DANGER),
        ("Today",    "Monthly Salary",      "Income",   "+$4,820", SUCCESS),
        ("Mar 18",   "Uber ride",           "Transport","-$14.20", DANGER),
        ("Mar 18",   "Grocery shopping",    "Food",     "-$67.40", DANGER),
        ("Mar 17",   "Netflix subscription","Bills",    "-$15.99", DANGER),
    ]
    ey = cy + 38
    rf = _font_regular(13)
    for date_, desc, cat, amt, col in entries:
        d.text((cx + 16, ey), date_, font=rf, fill=MUTED)
        d.text((cx + 90, ey), desc, font=rf, fill=TEXT)
        rrect(d, (cx + 360, ey - 2, cx + 440, ey + 18), 8, SURFACE)
        text_center(d, cat, cx + 360, ey + 1, 80, _font_regular(11), MUTED)
        bbox = d.textbbox((0, 0), amt, font=rf)
        aw2 = bbox[2] - bbox[0]
        d.text((cx + CW - 20 - aw2, ey), amt, font=rf, fill=col)
        ey += 28
        d.line((cx + 12, ey - 4, cx + CW - 12, ey - 4), fill=BORDER, width=1)

    return img


# ════════════════════════════════════════════════════════════════════════════════
# MOBILE ENTRIES  750 × 1334
# ════════════════════════════════════════════════════════════════════════════════
def make_mobile():
    W, H = 750, 1334
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ── status bar ────────────────────────────────────────────────────────────
    d.rectangle((0, 0, W, 44), fill=SURFACE)
    sf = _font_regular(13)
    d.text((20, 14), "9:41", font=sf, fill=TEXT)
    for i, icon in enumerate(["●", "●●●", "▶"]):
        d.text((W - 90 + i * 26, 14), icon, font=sf, fill=TEXT)

    # ── top nav ───────────────────────────────────────────────────────────────
    d.rectangle((0, 44, W, 100), fill=SURFACE)
    d.rectangle((0, 100, W, 101), fill=BORDER)
    bf = _font(20)
    d.text((20, 58), "⚡ BudgetPulse", font=bf, fill=PRIMARY)
    # hamburger
    for i in range(3):
        d.rectangle((W - 48, 62 + i * 9, W - 22, 65 + i * 9), fill=TEXT)

    # ── header card ──────────────────────────────────────────────────────────
    y = 112
    rrect(d, (12, y, W - 12, y + 120), 16,
          (30, 50, 100))  # gradient-ish dark blue
    d.rectangle((12, y, W - 12, y + 60), fill=(35, 55, 110))  # header fill
    mf = _font(15)
    d.text((28, y + 12), "March 2026", font=mf, fill=MUTED)
    hf = _font(26)
    d.text((28, y + 32), "Expenses", font=hf, fill=TEXT)
    # summary chips
    for i, (lbl, val, col) in enumerate([("Income", "$4,820", SUCCESS), ("Spent", "$3,147", DANGER), ("Saved", "$1,673", SUCCESS)]):
        cx = 28 + i * 226
        rrect(d, (cx, y + 78, cx + 200, y + 112), 10, SURFACE2, BORDER)
        d.text((cx + 10, y + 82), lbl, font=_font_regular(11), fill=MUTED)
        d.text((cx + 10, y + 96), val, font=_font(15), fill=col)

    y += 136

    # ── filter tabs ──────────────────────────────────────────────────────────
    tabs = ["All", "Expenses", "Income"]
    tw = W // len(tabs)
    for i, tab in enumerate(tabs):
        if i == 0:
            rrect(d, (i * tw + 8, y, (i + 1) * tw - 8, y + 38), 10, PRIMARY)
            text_center(d, tab, i * tw + 8, y + 10, tw - 16, _font(14), WHITE)
        else:
            rrect(d, (i * tw + 8, y, (i + 1) * tw - 8, y + 38), 10, SURFACE2, BORDER)
            text_center(d, tab, i * tw + 8, y + 10, tw - 16, _font_regular(14), MUTED)
    y += 50

    # ── entry cards ──────────────────────────────────────────────────────────
    entries = [
        ("Today",  "Coffee at Starbucks",     "Food & Drink",  "-$6.50",   DANGER,   "☕"),
        ("Today",  "Monthly Salary",          "Income",        "+$4,820",  SUCCESS,  "💵"),
        ("Mar 18", "Uber to office",          "Transport",     "-$14.20",  DANGER,   "🚗"),
        ("Mar 18", "Whole Foods grocery",     "Groceries",     "-$87.35",  DANGER,   "🛒"),
        ("Mar 17", "Netflix subscription",    "Subscriptions", "-$15.99",  DANGER,   "🎬"),
        ("Mar 17", "Electricity bill",        "Utilities",     "-$124.00", DANGER,   "⚡"),
        ("Mar 16", "Restaurant dinner",       "Food & Drink",  "-$52.40",  DANGER,   "🍽️"),
        ("Mar 16", "Amazon purchase",         "Shopping",      "-$34.99",  DANGER,   "📦"),
        ("Mar 15", "Gym membership",          "Health",        "-$49.00",  DANGER,   "🏋️"),
        ("Mar 15", "Freelance payment",       "Income",        "+$600",    SUCCESS,  "💼"),
    ]

    ef = _font_regular(14)
    df = _font_regular(12)
    for date_, desc, cat, amt, col, icon in entries:
        card_h = 76
        rrect(d, (12, y, W - 12, y + card_h), 14, SURFACE2, BORDER)

        # icon circle
        rrect(d, (24, y + 14, 72, y + 62), 20, SURFACE)
        ic = _font(22)
        d.text((30, y + 20), icon, font=ic, fill=TEXT)

        # desc + category
        d.text((84, y + 14), desc, font=ef, fill=TEXT)
        d.text((84, y + 38), f"{cat}  •  {date_}", font=df, fill=MUTED)

        # amount
        bbox = d.textbbox((0, 0), amt, font=_font(16))
        aw = bbox[2] - bbox[0]
        d.text((W - 28 - aw, y + 26), amt, font=_font(16), fill=col)

        y += card_h + 10
        if y > H - 120:
            break

    # ── bottom nav ────────────────────────────────────────────────────────────
    d.rectangle((0, H - 90, W, H), fill=SURFACE)
    d.rectangle((0, H - 91, W, H - 90), fill=BORDER)
    nav = [("📊", "Dashboard"), ("💰", "Entries"), ("➕", "Add"), ("📈", "Reports"), ("⚙️", "Settings")]
    nw = W // len(nav)
    for i, (ico, lbl) in enumerate(nav):
        nx = i * nw
        col = PRIMARY if i == 1 else MUTED
        if i == 2:  # FAB
            rrect(d, (nx + nw // 2 - 28, H - 84, nx + nw // 2 + 28, H - 28), 28, PRIMARY)
            ic2 = _font(22)
            d.text((nx + nw // 2 - 12, H - 78), ico, font=ic2, fill=WHITE)
        else:
            d.text((nx + nw // 2 - 12, H - 80), ico, font=_font(18), fill=col)
            d.text((nx + nw // 2 - 20, H - 48), lbl, font=_font_regular(11), fill=col)

    return img


# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "static", "screenshots")
    os.makedirs(out_dir, exist_ok=True)

    desk = make_desktop()
    desk_path = os.path.join(out_dir, "desktop-dashboard.png")
    desk.save(desk_path, "PNG", optimize=True)
    print(f"Saved {desk_path}  ({desk.size[0]}×{desk.size[1]})")

    mob = make_mobile()
    mob_path = os.path.join(out_dir, "mobile-entries.png")
    mob.save(mob_path, "PNG", optimize=True)
    print(f"Saved {mob_path}  ({mob.size[0]}×{mob.size[1]})")
