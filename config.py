# ============================================================
#  QS MARKETPLACE — DATABASE CONFIGURATION
# ============================================================
#  DEFAULT: SQLite (no setup needed, just run the app)
#  TO USE MYSQL: Set USE_MYSQL = True and fill in the details
# ============================================================
import os

# ── Database Choice ─────────────────────────────────────────
USE_MYSQL = False   # Set to True to switch to MySQL

# ── MySQL Settings (only used when USE_MYSQL = True) ────────
MYSQL_HOST     = "localhost"
MYSQL_PORT     = 3306
MYSQL_USER     = "root"
MYSQL_PASSWORD = "your_password_here"
MYSQL_DATABASE = "qs_marketplace"

# ── App Settings ────────────────────────────────────────────
SECRET_KEY       = "qs-marketplace-secret-2024-xK9pL2mN"
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER    = os.path.join("/tmp", "uploads")
COMMISSION_RATE  = 5.0   # Default commission percentage

# ── Seed Control ────────────────────────────────────────────
SEED_FLAG_FILE = "/tmp/.seeded"

# ── Build DB URL ─────────────────────────────────────────────
if USE_MYSQL:
    DATABASE_URL = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
else:
    DATABASE_URL = "sqlite:////tmp/marketplace.db"
