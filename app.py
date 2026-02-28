import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import bcrypt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Volunteer Portal", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { font-weight: 600; font-size: 16px; }
.block-container { padding-top: 1rem; }
.stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"],
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"],
    })
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------------- AUTH FUNCTIONS ----------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def get_user_by_mobile(mobile):
    users = db.collection("users").where("mobile", "==", mobile).stream()
    for user in users:
        data = user.to_dict()
        data["id"] = user.id
        return data
    return None

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# ---------------- SIDEBAR ----------------
st.sidebar.title("🤝 Volunteer Portal")

if not st.session_state.logged_in:
    menu = st.sidebar.radio("Menu", ["Public Notice Board", "Login"])
else:
    menu = st.sidebar.radio("Navigation", [
        "Dashboard",
        "Teams",
        "Meetings",
        "Plan Next Meeting",
        "Planning",
        "Reports",
        "Public Notice Board",
        "Logout"
    ])

# ---------------- PUBLIC NOTICE BOARD ----------------
if menu == "Public Notice Board":
    st.title("📢 Public Notice Board")

    notices = db.collection("notices").order_by("time").stream()
    for n in notices:
        data = n.to_dict()
        st.markdown(f"### 🗞 {data.get('notice')}")
        st.caption(f"Posted by: {data.get('posted_by')} | {data.get('time')}")
        st.divider()

# ---------------- LOGIN ----------------
elif menu == "Login":
    st.title("🔐 Login")

    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = get_user_by_mobile(mobile)

        if not user:
            st.error("User not found")
        elif not user.get("is_approved", False):
            st.warning("Account not approved by admin yet.")
        elif user.get("is_blocked", False):
            st.error("Your account is blocked.")
        elif check_password(password, user["password_hash"]):
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user_id = user["id"]
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Wrong Password")

# ---------------- LOGOUT ----------------
elif menu == "Logout":
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.rerun()

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    st.title(f"📊 {st.session_state.role} Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        total_teams = len(list(db.collection("teams").stream()))
        st.metric("Total Team Entries", total_teams)

    with col2:
        total_meetings = len(list(db.collection("meetings").stream()))
        st.metric("Total Meetings Recorded", total_meetings)

# ---------------- TEAMS ----------------
elif menu == "Teams":
    st.title("👥 Team Dashboard")

    selected_team = st.selectbox("Select Team", [
        "Jury Team", "Task Team", "Monitoring Team", "Data Team"
    ])

    with st.form("team_form"):
        name = st.text_input("Member Name")
        details = st.text_area("Details / Work Description")
        submit = st.form_submit_button("Save")

        if submit:
            db.collection("teams").add({
                "team": selected_team,
                "name": name,
                "details": details,
                "created_by": st.session_state.role
            })
            st.success("Saved Successfully")

    st.divider()
    st.subheader("Team Records")

    records = db.collection("teams").where("team", "==", selected_team).stream()
    for r in records:
        data = r.to_dict()
        st.write(f"👤 {data.get('name')} — {data.get('details')}")

# ---------------- MEETINGS ----------------
elif menu == "Meetings":
    st.title("📅 Meeting Attendance")

    with st.form("attendance_form"):
        name = st.text_input("Your Name")
        attending = st.radio("Will You Attend?", ["Yes", "No"])
        reason = st.text_area("Reason (if No)")
        submit = st.form_submit_button("Submit")

        if submit:
            db.collection("meetings").add({
                "name": name,
                "attending": attending,
                "reason": reason,
                "role": st.session_state.role
            })
            st.success("Attendance Recorded")

# ---------------- PLAN NEXT MEETING ----------------
elif menu == "Plan Next Meeting":
    st.title("🗓 Plan Next Meeting")

    with st.form("next_meeting_form"):
        organizer = st.text_input("Organizer Name")
        date = st.date_input("Meeting Date")
        day = st.selectbox("Day", [
            "Monday","Tuesday","Wednesday","Thursday",
            "Friday","Saturday","Sunday"
        ])
        time = st.time_input("Meeting Time")
        agenda = st.text_area("Meeting Agenda")

        submit = st.form_submit_button("Save Meeting")

        if submit:
            db.collection("next_meeting").add({
                "organizer": organizer,
                "date": str(date),
                "day": day,
                "time": str(time),
                "agenda": agenda,
                "created_by": st.session_state.role,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success("Next Meeting Scheduled")

    st.divider()
    st.subheader("Upcoming Meetings")

    meetings = db.collection("next_meeting").order_by("created_at").stream()
    for m in meetings:
        data = m.to_dict()
        st.markdown(f"### 📍 {data.get('agenda')}")
        st.write(f"👤 Organizer: {data.get('organizer')}")
        st.write(f"📅 {data.get('date')} ({data.get('day')})")
        st.write(f"⏰ {data.get('time')}")
        st.divider()

# ---------------- PLANNING ----------------
elif menu == "Planning":
    st.title("📈 Planning Progress")

    plan = st.text_area("Plan Description")
    progress = st.slider("Completion %", 0, 100, 40)

    st.progress(progress)

    if st.button("Save Planning"):
        db.collection("planning").add({
            "plan": plan,
            "progress": progress,
            "role": st.session_state.role
        })
        st.success("Planning Saved")

# ---------------- REPORTS ----------------
elif menu == "Reports":
    st.title("📊 Reports Overview")

    records = db.collection("teams").stream()
    data = [doc.to_dict() for doc in records]

    if len(data) > 0:
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.bar_chart(df["team"].value_counts())
    else:
        st.info("No Data Available")

# ---------------- POST NOTICE ----------------
if st.session_state.logged_in:
    with st.sidebar.expander("📢 Post Notice"):
        notice_text = st.text_area("Write Notice")
        if st.button("Post Notice"):
            db.collection("notices").add({
                "notice": notice_text,
                "posted_by": st.session_state.role,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.success("Notice Posted")
           
