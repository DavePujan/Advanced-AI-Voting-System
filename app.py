import streamlit as st
import cv2
import numpy as np
import time
import pandas as pd
from PIL import Image
from database.db import *
from vision.face_recog import *
from vision.liveness import check_liveness, reset_liveness

# Initialize database
try:
    init_db()
except Exception as e:
    st.error(f"❌ Database Error: {e}")

# Validates and reloads embeddings from DB
def get_known_faces():
    voters = get_all_voters_with_embeddings()
    known_faces = {}
    for v in voters:
        if v['face_embedding']:
            try:
                known_faces[v['username']] = pickle.loads(v['face_embedding'])
            except:
                pass
    return known_faces

st.set_page_config(page_title="Advanced AI Voting System", layout="centered")

st.title("🗳️ Advanced AI Voting System")

# Session State for User
if "user" not in st.session_state:
    st.session_state.user = None

# --- SIDEBAR MENU ---
if st.session_state.user:
    # Authenticated Menu
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Logout"])
else:
    # Public Menu
    # Public Menu
    menu = st.sidebar.selectbox("Menu", ["Login", "Register User", "Register Organization"])

# --- DEBUGGER (Remove before final production) ---
with st.sidebar.expander("🛠️ Debug Info"):
    st.write(f"**Target Host:** `{DB_HOST}`")
    
    if DB_HOST == "localhost":
        st.error("⚠️ Falling back to localhost! Cloud DB not connected.")
        st.write("Reason: `st.secrets` missing or keys don't match `config.py`.")
    else:
        st.success("✅ targeted Cloud DB")

    # Show available top-level keys (safely)
    try:
        if st.secrets:
            st.write("**Available Secret Sections:**", list(st.secrets.keys()))
            if "mysql" in st.secrets:
                 st.write("**Keys in [mysql]:**", list(st.secrets["mysql"].keys()))
        else:
             st.warning("No secrets found at all.")
    except Exception as e:
        st.write(f"Error reading secrets: {e}")
# -------------------------------------------------

# ==========================
# PUBLIC ROUTES
# ==========================

if menu == "Register Organization":
    st.header("🏢 Register New Organization")
    st.info("Create a space for your Company, NGO, or College.")
    
    with st.form("org_form"):
        org_name = st.text_input("Organization Name (Unique)")
        org_type = st.selectbox("Type", ["Company", "NGO", "College", "Community", "Other"])
        submit_org = st.form_submit_button("Create Organization")
        
        if submit_org:
            if org_name:
                if create_org(org_name, org_type):
                    st.success(f"Organization '{org_name}' created successfully! You can now register users under it.")
                else:
                    st.error("Organization name already exists or creation failed.")
            else:
                st.warning("Please enter organization name.")

elif menu == "Register User":
    st.header("👤 Register New User")
    
    # 1. Select Organization
    orgs = get_all_orgs()
    org_names = {org['name']: org['id'] for org in orgs}
    
    if not orgs:
        st.warning("No organizations found. Please 'Register Organization' first.")
    else:
        selected_org_name = st.selectbox("Select Organization", list(org_names.keys()))
        selected_org_id = org_names[selected_org_name]
        
        # 2. Select Role
        role = st.selectbox("Apply for Position / Role", ["Employee", "Admin"])
        
        with st.form("register_form"):
            st.subheader("Account Details")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name")
                username = st.text_input("Username")
            with col2:
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")
                
            st.subheader("Face Registration")
            st.write("Please look at the camera and take a clear photo.")
            img_file = st.camera_input("Capture Face", label_visibility="hidden")
            
            submit_button = st.form_submit_button("Create Account")

            if submit_button:
                if not (name and username and email and password and img_file):
                    st.warning("Please fill all fields and capture your face.")
                elif password != confirm_pw:
                    st.error("Passwords do not match!")
                else:
                    img = Image.open(img_file)
                    img_np = np.array(img)
                    
                    with st.spinner("Processing..."):
                        # Load current DB faces
                        known_faces = get_known_faces()
                        
                        # 0. Check if Face Already Exists
                        existing_user = check_face_exists(img_np, known_faces)
                        if existing_user:
                            st.error(f"Face already registered as user: {existing_user}. Please login.")
                        else:
                            # 1. Register Face 
                            embedding = register(img_np)
                            if embedding is not None:
                                # Serialize embedding
                                embedding_blob = pickle.dumps(embedding)
                                
                                # 2. Save to DB
                                if add_voter(name, email, password, username, role, selected_org_id, embedding_blob):
                                    st.success("Account Created Successfully! Please Login.")
                                else:
                                    st.error("Registration failed. Email or Username might already exist.")
                            else:
                                st.error("Face detection failed. Please try again with better lighting.")

# ...



elif menu == "Login":
    st.header("Login")
    
    # 1. Select Organization
    orgs = get_all_orgs()
    org_names = {org['name']: org['id'] for org in orgs}
    
    if not orgs:
        st.warning("No organizations found.")
    else:
        selected_org_name = st.selectbox("Select Organization", list(org_names.keys()))
        selected_org_id = org_names[selected_org_name]
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user = authenticate_voter(email, password, selected_org_id)
            if user:
                st.session_state.user = user
                st.success(f"Welcome back, {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid Credentials or Organization.")

# ==========================
# AUTHENTICATED ROUTES
# ==========================

elif menu == "Logout":
    st.session_state.user = None
    st.rerun()

elif menu == "Dashboard":
    user = st.session_state.user
    
    # Header with Org Details
    org = get_org_by_id(user['org_id'])
    st.title(f"{org['name']} - {user['role']} Panel")
    
    # --- ADMIN DASHBOARD ---
    if user['role'] == "Admin":
        tab1, tab2, tab3, tab4 = st.tabs(["Create Election", "Manage Candidates", "View Results", "Manage Employees"])
        
        with tab1:
            st.subheader("Create New Election Form")
            st.info("Examples: 'Presidential Election', 'Secretary Post', 'Board Member 2026'")
            election_name = st.text_input("Election Name")
            if st.button("Create Election"):
                if create_election(election_name, user['org_id']):
                    st.success(f"Election '{election_name}' created!")
                else:
                    st.error("Failed to create election.")

        with tab2:
            st.subheader("Manage Candidates")
            
            # Select Active Election
            elections = get_org_elections(user['org_id'])
            if not elections:
                st.warning("Please create an election first.")
            else:
                elec_options = {e['name']: e['id'] for e in elections}
                select_elec_name = st.selectbox("Select Election", list(elec_options.keys()))
                select_elec_id = elec_options[select_elec_name]
                
                # Add Candidate to Selected Election
                new_candidate = st.text_input("Add Candidate Name")
                if st.button("Add Candidate"):
                    if add_candidate(new_candidate, user['org_id'], select_elec_id):
                        st.success(f"Candidate added to {select_elec_name}.")
                        st.rerun()
                    else:
                        st.error("Failed to add.")
                
                st.write("---")
                st.write(f"**Current Candidates for {select_elec_name}:**")
                candidates = get_election_candidates(select_elec_id)
                if candidates:
                    for cand in candidates:
                        col1, col2 = st.columns([4, 1])
                        col1.write(cand['name'])
                        if col2.button("🗑️", key=f"del_{cand['id']}"):
                            delete_candidate(cand['id'], user['org_id'])
                            st.rerun()
                else:
                    st.info("No candidates added yet.")

        with tab3:
            st.subheader("Voting Results")
            elections = get_org_elections(user['org_id'])
            if not elections:
                st.info("No elections found.")
            else:
                elec_options = {e['name']: e['id'] for e in elections}
                res_elec_name = st.selectbox("View Results For", list(elec_options.keys()), key="res_select")
                res_elec_id = elec_options[res_elec_name]
                
                results = get_election_results(res_elec_id)
                if results:
                    import pandas as pd
                    df = pd.DataFrame(results)
                    st.bar_chart(df.set_index('candidate_name')['count'])
                    st.table(df)
                else:
                    st.info("No votes cast yet.")
                    
                st.subheader("Attendance Log")
                att = get_election_attendance(res_elec_id)
                if att:
                    st.table(pd.DataFrame(att))
                else:
                    st.info("No attendance records.")

        with tab4:
            st.subheader("Employees List")
            emps = get_org_employees(user['org_id'])
            if emps:
                st.table(pd.DataFrame(emps))

    # --- EMPLOYEE DASHBOARD (VOTING) ---
    else:
        st.subheader("Cast Your Vote")
        
        # 1. Select Available Election
        elections = get_org_elections(user['org_id'])
        if not elections:
            st.warning("No active elections found for your organization.")
        else:
            elec_options = {e['name']: e['id'] for e in elections}
            vote_elec_name = st.selectbox("Select Election to Vote", list(elec_options.keys()))
            vote_elec_id = elec_options[vote_elec_name]
            
            st.write(f"--- Voting for: **{vote_elec_name}** ---")

            if has_voted(user['email'], user['org_id'], vote_elec_id):
                st.success("✅ You have already voted in this election. Thank you!")
            else:
                candidates = get_election_candidates(vote_elec_id)
                if not candidates:
                    st.warning("No candidates available for this election yet.")
                else:
                    st.info("To ensure security, please verify your face before voting.")
                    
                    # Use Streamlit's native camera input (works on Cloud & Local)
                    img_file_verify = st.camera_input("Verify Identity", key="verify_cam")
                    
                    if img_file_verify is not None:
                        img = Image.open(img_file_verify)
                        img_np = np.array(img)
                        
                        # Check Face Match
                        known_faces = get_known_faces()
                        recognized_user = recognize(img_np, known_faces)
                        
                        if recognized_user == user['username']:
                            st.success("Identity Verified!")
                            
                            with st.form("vote_form"):
                                cand_options = {c['name']: c['id'] for c in candidates}
                                choice = st.radio("Choose Candidate", list(cand_options.keys()))
                                
                                if st.form_submit_button("Submit Vote"):
                                    if save_vote(user['email'], cand_options[choice], user['org_id'], vote_elec_id):
                                        mark_attendance(user['email'], user['org_id'], vote_elec_id)
                                        st.balloons()
                                        st.success("Vote Cast Successfully!")
                                        time.sleep(2)
                                        st.rerun()
                                    else:
                                        st.error("Failed to save vote. Please try again.")
                        else:
                            st.error(f"Face recognized as {recognized_user}, but you are logged in as {user['username']}.") if recognized_user else st.warning("Face not recognized. Please move closer or try better lighting.")
