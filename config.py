import streamlit as st

# MySQL Configuration

# Try to load from Streamlit Secrets (for Cloud Deployment)
try:
    DB_HOST = st.secrets["DB_HOST"]
    DB_USER = st.secrets["DB_USER"]
    DB_PASS = st.secrets["DB_PASS"]
    DB_NAME = st.secrets["DB_NAME"]
    DB_PORT = int(st.secrets.get("DB_PORT", 3306)) # Default to 3306
except (FileNotFoundError, KeyError):
    # Fallback to Local Configuration (for Development)
    DB_HOST = "localhost"
    DB_USER = "root"
    
    # ⚠️ IMPORTANT: Update this password to match your local MySQL setup
    # If you get "Access denied", it's likely because this password is wrong.
    DB_PASS = "root" 
    
    DB_NAME = "voting_system"
    DB_PORT = 3306

# Liveness Config (Legacy param, kept for compatibility if needed)
EYE_AR_THRESH = 0.30
