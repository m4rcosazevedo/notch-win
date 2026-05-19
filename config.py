from pathlib import Path

try:
    from plyer import notification as plyer_notify
    PLYER_OK = True
except Exception:
    PLYER_OK = False

try:
    import winsound as _winsound
    _WINSOUND_OK = True
except ImportError:
    _winsound = None
    _WINSOUND_OK = False

BASE_DIR      = Path(__file__).parent
MONSTERS_DIR  = BASE_DIR / "assets" / "monsters"
QSS_PATH      = BASE_DIR / "ui" / "styles.qss"
SETTINGS_PATH = BASE_DIR / ".notch_settings.json"
NOTES_PATH    = BASE_DIR / ".notch_notes.txt"
TODO_PATH     = BASE_DIR / ".notch_todo.json"

# (key, label, pill_bg, border, accent_rgb, mode, icon_rgba)
COLOR_PRESETS = [
    # ── Dark ──────────────────────────────────────────────────────────────────
    ("space-gray", "Space Gray",  "rgba(14,14,14,248)",    "rgba(255,255,255,0.07)", (180,180,180), "dark",  (220,220,220,190)),
    ("graphite",   "Graphite",    "rgba(28,28,30,248)",    "rgba(255,255,255,0.10)", (200,200,200), "dark",  (220,220,220,190)),
    ("midnight",   "Midnight",    "rgba(10,16,38,248)",    "rgba(80,130,255,0.18)",  ( 74,122,255), "dark",  (180,210,255,200)),
    ("ocean",      "Ocean",       "rgba(5,20,35,248)",     "rgba(0,160,230,0.18)",   (  0,170,240), "dark",  (150,220,255,200)),
    ("viridian",   "Viridian",    "rgba(8,26,16,248)",     "rgba(48,210,88,0.18)",   ( 48,209, 88), "dark",  (170,240,190,200)),
    ("forest",     "Forest",      "rgba(5,20,10,248)",     "rgba(50,180,80,0.15)",   ( 50,180, 80), "dark",  (160,230,170,200)),
    ("grape",      "Grape",       "rgba(24,10,44,248)",    "rgba(190,100,255,0.18)", (155, 89,182), "dark",  (210,170,255,200)),
    ("rosewood",   "Rosewood",    "rgba(38,8,14,248)",     "rgba(255,70,90,0.18)",   (255, 69, 58), "dark",  (255,180,180,200)),
    ("ember",      "Ember",       "rgba(30,12,5,248)",     "rgba(255,120,40,0.20)",  (255,120, 40), "dark",  (255,205,155,200)),
    ("obsidian",   "Obsidian",    "rgba(18,18,22,248)",    "rgba(150,150,255,0.12)", (120,120,200), "dark",  (200,200,230,190)),
    # ── Light ─────────────────────────────────────────────────────────────────
    ("arctic",     "Arctic",      "rgba(245,248,252,235)", "rgba(0,0,0,0.12)",       ( 80,120,200), "light", ( 30, 30, 40,200)),
    ("sand",       "Sand",        "rgba(248,242,228,235)", "rgba(0,0,0,0.10)",       (160,120, 60), "light", ( 60, 45, 20,200)),
    ("blossom",    "Blossom",     "rgba(252,236,244,235)", "rgba(200,80,140,0.20)",  (200, 80,140), "light", (100, 20, 60,200)),
    ("sky",        "Sky",         "rgba(228,242,255,235)", "rgba(60,130,230,0.20)",  ( 60,130,230), "light", ( 20, 50,130,200)),
    ("mint",       "Mint",        "rgba(228,248,236,235)", "rgba(40,180,100,0.20)",  ( 40,180,100), "light", ( 10, 80, 40,200)),
    ("lavender",   "Lavender",    "rgba(236,232,252,235)", "rgba(130,100,220,0.20)", (130,100,220), "light", ( 60, 30,130,200)),
    ("cream",      "Cream",       "rgba(252,248,238,235)", "rgba(160,130,60,0.15)",  (160,130, 60), "light", ( 80, 65, 20,200)),
]

POMO_PRESETS = [
    ("15 min",  15,  5, 10),
    ("20 min",  20,  5, 10),
    ("25 min",  25,  5, 15),
    ("30 min",  30, 10, 20),
    ("45 min",  45, 15, 25),
    ("60 min",  60, 20, 30),
]

MENU_QSS = """
QMenu {
    background-color: rgba(28,28,30,252);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 12px;
    padding: 6px 4px;
    font-family: "SF Pro Text","Segoe UI",sans-serif;
    font-size: 12px;
    color: #e5e5ea;
}
QMenu::item {
    padding: 7px 20px 7px 14px;
    border-radius: 8px;
    margin: 1px 4px;
    color: #e5e5ea;
}
QMenu::item:selected { background: rgba(255,255,255,0.10); color:#fff; }
QMenu::item:disabled { color: rgba(255,255,255,0.28); }
QMenu::separator     { height:1px; background:rgba(255,255,255,0.10); margin:4px 10px; }
"""


def notify(title: str, message: str):
    if PLYER_OK:
        try:
            plyer_notify.notify(title=title, message=message, app_name="Notch", timeout=4)
        except Exception:
            pass
