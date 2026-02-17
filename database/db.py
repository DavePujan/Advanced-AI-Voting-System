import mysql.connector
import hashlib
from config import DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT
import streamlit as st

import os

def get_db_connection():
    try:
        config = {
            "host": DB_HOST,
            "user": DB_USER,
            "password": DB_PASS,
            "database": DB_NAME,
            "port": DB_PORT
        }
        
        # Check for Aiven CA Certificate (ca.pem)
        ssl_status = "Not Found"
        if os.path.exists("ca.pem"):
            config["ssl_ca"] = os.path.abspath("ca.pem")
            config["ssl_disabled"] = False
            config["ssl_verify_cert"] = True
            ssl_status = f"Found at {os.path.abspath('ca.pem')}"
        
        # Debugging Connection Params (safely)
        masked_pw = DB_PASS[:3] + "*" * (len(DB_PASS)-6) + DB_PASS[-3:] if len(DB_PASS) > 6 else "***"
        st.write(f"🔌 **Connecting to:** `{DB_HOST}:{DB_PORT}`")
        st.write(f"👤 **User:** `{DB_USER}` | 🔑 **Pass:** `{masked_pw}` (Len: {len(DB_PASS)})")
        st.write(f"🔒 **SSL CA Status:** {ssl_status}")
        st.write(f"📂 **CWD:** `{os.getcwd()}`")

        # Hint for Aiven users
        if "aiven" in DB_HOST:
             st.info("💡 **Aiven Tip:** New accounts default to 'Allow all IPs', but if you edited 'Allowed IP Addresses', add `0.0.0.0/0` to allow Streamlit Cloud.")
             st.info("💡 **Password Check:** Did you click 'Reset Password' recently? If so, update your secrets!")

        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        st.error(f"❌ Connection Failed: {err}")
        return None

# ... (init_db unchanged for now, handled by app.py try/catch)

# --- Organization Functions ---
def create_org(name, org_type):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO organizations(name, type) VALUES(%s, %s)", (name, org_type))
            conn.commit()
            org_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return org_id
        except mysql.connector.Error as err:
            st.error(f"⚠️ Create Org Failed: {err}")
            return None
    return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    try:
        config = {
            "host": DB_HOST,
            "user": DB_USER,
            "password": DB_PASS,
            "port": DB_PORT
        }
        if os.path.exists("ca.pem"):
            config["ssl_ca"] = "ca.pem"
            config["ssl_disabled"] = False

        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # 1. Organizations Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) UNIQUE,
            type VARCHAR(50)
        )
        """)

        # 2. Voters/Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS voters(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255),
            username VARCHAR(255) UNIQUE,
            role VARCHAR(50),
            org_id INT,
            face_embedding LONGBLOB,  -- Store pickled numpy array
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
        """)
        
        # 3. Elections Table (NEW)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS elections(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            org_id INT,
            status VARCHAR(50) DEFAULT 'Active', -- 'Active', 'Closed'
            FOREIGN KEY (org_id) REFERENCES organizations(id)
        )
        """)

        # 4. Candidates Table (Modified to link to Election)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            org_id INT,
            election_id INT,
            FOREIGN KEY (org_id) REFERENCES organizations(id),
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
        """)

        # 5. Votes Table (Modified to link to Election)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes(
            voter_email VARCHAR(255),
            candidate_id INT,
            org_id INT,
            election_id INT,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (org_id) REFERENCES organizations(id),
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
        """)

        # 6. Attendance Table (Modified to link to Election)
        # attendance is now per election
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            voter_email VARCHAR(255),
            org_id INT,
            election_id INT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (org_id) REFERENCES organizations(id),
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
        """)
        
        # --- Migration Logic ---
        cursor.execute("DESCRIBE voters")
        voter_cols = [c[0] for c in cursor.fetchall()]
        if 'face_embedding' not in voter_cols:
            cursor.execute("ALTER TABLE voters ADD COLUMN face_embedding LONGBLOB")

        cursor.execute("DESCRIBE candidates")
        cand_cols = [c[0] for c in cursor.fetchall()]
        if 'election_id' not in cand_cols:
            cursor.execute("ALTER TABLE candidates ADD COLUMN election_id INT")
            
        cursor.execute("DESCRIBE votes")
        vote_cols = [c[0] for c in cursor.fetchall()]
        if 'election_id' not in vote_cols:
            cursor.execute("ALTER TABLE votes ADD COLUMN election_id INT")

        cursor.execute("DESCRIBE attendance")
        att_cols = [c[0] for c in cursor.fetchall()]
        if 'election_id' not in att_cols:
            cursor.execute("ALTER TABLE attendance ADD COLUMN election_id INT")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
    except mysql.connector.Error as err:
        print(f"Error initializing database: {err}")

# --- Organization Functions ---
def create_org(name, org_type):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO organizations(name, type) VALUES(%s, %s)", (name, org_type))
            conn.commit()
            org_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return org_id
        except mysql.connector.Error as err:
            return None
    return None

def get_all_orgs():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, type FROM organizations")
            orgs = cursor.fetchall()
            cursor.close()
            conn.close()
            return orgs
        except mysql.connector.Error:
            return []
    return []

def get_org_by_id(org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM organizations WHERE id=%s", (org_id,))
            org = cursor.fetchone()
            cursor.close()
            conn.close()
            return org
        except mysql.connector.Error:
            return None
    return None

# --- User/Voter Functions ---
def add_voter(name, email, password, username, role, org_id, face_embedding=None):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            hashed_pw = hash_password(password)
            # face_embedding is expected to be bytes (pickled)
            cursor.execute(
                "INSERT INTO voters(name, email, password, username, role, org_id, face_embedding) VALUES(%s, %s, %s, %s, %s, %s, %s)", 
                (name, email, hashed_pw, username, role, org_id, face_embedding)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as err:
            return False
    return False

def get_all_voters_with_embeddings():
    """
    Fetches all voters with their face embeddings.
    Returns list of dicts: {username, face_embedding (bytes), ...}
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT username, face_embedding FROM voters WHERE face_embedding IS NOT NULL")
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return users
        except mysql.connector.Error:
            return []
    return []

def authenticate_voter(email, password, org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            hashed_pw = hash_password(password)
            cursor.execute(
                "SELECT * FROM voters WHERE email=%s AND password=%s AND org_id=%s", 
                (email, hashed_pw, org_id)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except mysql.connector.Error as err:
            return None
    return None

def get_org_employees(org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name, email, role, username FROM voters WHERE org_id=%s", (org_id,))
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            return users
        except:
            return []
    return []

# --- Election Functions (NEW) ---
def create_election(name, org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO elections(name, org_id) VALUES(%s, %s)", (name, org_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except:
            return False
    return False

def get_org_elections(org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM elections WHERE org_id=%s", (org_id,))
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        except:
            return []
    return []

# --- Candidate Functions ---

def add_candidate(name, org_id, election_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO candidates(name, org_id, election_id) VALUES(%s, %s, %s)", (name, org_id, election_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except:
            return False
    return False

def get_election_candidates(election_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM candidates WHERE election_id=%s", (election_id,))
            candidates = cursor.fetchall()
            cursor.close()
            conn.close()
            return candidates
        except:
            return []
    return []
    
# Keep legacy for backward compat if needed, but better to use election specific
def get_org_candidates(org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, election_id FROM candidates WHERE org_id=%s", (org_id,))
            candidates = cursor.fetchall()
            cursor.close()
            conn.close()
            return candidates
        except:
            return []
    return []

def delete_candidate(candidate_id, org_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM candidates WHERE id=%s AND org_id=%s", (candidate_id, org_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except:
            return False
    return False

# --- Voting/Attendance Functions ---

def mark_attendance(email, org_id, election_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Insert attendance for specific election
            cursor.execute("INSERT IGNORE INTO attendance(voter_email, org_id, election_id) VALUES(%s, %s, %s)", (email, org_id, election_id))
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            print(f"Error marking attendance: {err}")

def has_voted(email, org_id, election_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM votes WHERE voter_email=%s AND org_id=%s AND election_id=%s", (email, org_id, election_id))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        except mysql.connector.Error as err:
            return False
    return False

def save_vote(email, candidate_id, org_id, election_id):
    conn = get_db_connection()
    if conn:
        try:
            print(f"DEBUG: Saving vote for {email}, cand: {candidate_id}, org: {org_id}, elec: {election_id}")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO votes(voter_email, candidate_id, org_id, election_id) VALUES(%s, %s, %s, %s)", (email, candidate_id, org_id, election_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except mysql.connector.Error as err:
            print(f"Error saving vote: {err}")
            return False
    return False

def get_election_results(election_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT c.name as candidate_name, COUNT(v.voter_email) as count 
                FROM candidates c 
                LEFT JOIN votes v ON c.id = v.candidate_id 
                WHERE c.election_id = %s 
                GROUP BY c.id
            """
            cursor.execute(query, (election_id,))
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        except mysql.connector.Error as err:
            return []
    return []

def get_election_attendance(election_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT voter_email, timestamp FROM attendance WHERE election_id=%s", (election_id,))
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        except:
            return []
    return []

# Initialize DB on module load
try:
    init_db()
except:
    pass
