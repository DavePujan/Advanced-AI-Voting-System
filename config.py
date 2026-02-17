import streamlit as st

# MySQL Configuration

def load_db_config():
    """
    Attempts to load DB config from st.secrets, handling multiple formats
    (flat keys, nested [mysql] section, key aliases).
    """
    try:
        # 1. Determine source (Root or [mysql] section)
        source = st.secrets
        if "mysql" in st.secrets:
            source = st.secrets["mysql"]
            
        # 2. Extract with fallback aliases
        host = source.get("DB_HOST")
        
        user = source.get("DB_USER") or source.get("DB_USERNAME")
        
        password = source.get("DB_PASS") or source.get("DB_PASSWORD") or source.get("DB_KEY")
        
        name = source.get("DB_NAME") or source.get("DB_DATABASE")
        
        port = source.get("DB_PORT", 3306)

        # 3. Validate
        if not (host and user and password and name):
            raise KeyError(f"Missing one or more required keys. Found: Host={host}, User={user}, Name={name}")

        return str(host).strip(), str(user).strip(), str(password).strip(), str(name).strip(), int(port)

    except (FileNotFoundError, KeyError) as e:
        # Fallback to Local Configuration (Development)
        return "localhost", "root", "root", "voting_system", 3306

DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT = load_db_config()

# Liveness Config (Legacy param, kept for compatibility if needed)
EYE_AR_THRESH = 0.30
