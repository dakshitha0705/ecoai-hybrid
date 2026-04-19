# backend/config.py
import os

# ─────────────────────────────────────────────────────────────────
# Mininet server address
# When running in WSL, localhost from Windows reaches WSL on the same port
# ─────────────────────────────────────────────────────────────────
MININET_BASE_URL = os.getenv("MININET_URL", "http://localhost:9000")
MININET_TIMEOUT_SECONDS = 3

# ─────────────────────────────────────────────────────────────────
# JWT settings
# ─────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_ecoai_secret_2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ─────────────────────────────────────────────────────────────────
# Simulated users (in production, use a database)
# ─────────────────────────────────────────────────────────────────
# Passwords here are bcrypt hashed. Plaintext: viewer123, operator123, admin123
USERS_DB = {
    "viewer": {
        "username": "viewer",
        "hashed_password": "$2b$12$KIX7v6GqFpBpTAT5n3rNH.gNNvHGkJYp0kXd6PjGl8mZl3Y/ZhsLW",
        "role": "viewer",
    },
    "operator": {
        "username": "operator",
        "hashed_password": "$2b$12$K9pEgfzYvCQXimB2IumzxeZ2yCmfmAEgYUdHt5J0w6xKJzO8a2TZi",
        "role": "operator",
    },
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$G4RGUDtIjWQF3h2p3L9wCeYM8jfIL8L4C5Hw7JRnHQfmRuSGDl1kC",
        "role": "admin",
    },
}
