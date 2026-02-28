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
    try:
        if not hashed:
            return False
        if isinstance(hashed, str):
            hashed = hashed.encode()
        return bcrypt.checkpw(password.encode(), hashed)
    except Exception:
        return False
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
        "Admin Panel",
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
        st.divider()
    st.subheader("📝 New Registration")

    with st.form("registration_form"):
        reg_name = st.text_input("Full Name")
        reg_father = st.text_input("Father Name")
        reg_mobile = st.text_input("Mobile Number")

        reg_submit = st.form_submit_button("Submit Registration")

        if reg_submit:
            existing_user = db.collection("users").where("mobile", "==", reg_mobile).stream()
            if list(existing_user):
                st.warning("User already registered. Please login.")
            else:
                existing_request = db.collection("registration_requests").where("mobile", "==", reg_mobile).stream()
                if list(existing_request):
                    st.warning("Registration already pending.")
                else:
                    db.collection("registration_requests").add({
                        "name": reg_name,
                        "father_name": reg_father,
                        "mobile": reg_mobile,
                        "status": "pending",
                        "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    st.success("Registration request submitted. Wait for admin approval.")
        
  #admin---panel#
# ---------------- ADMIN PANEL ----------------
elif menu == "Admin Panel":

    if st.session_state.role != "Admin":
        st.error("Access Denied")
    else:
        st.title("👑 Admin Approval Panel")

        requests = db.collection("registration_requests").where("status", "==", "pending").stream()

        for req in requests:
            data = req.to_dict()
            doc_id = req.id

            st.subheader(data.get("name"))
            st.write("Father Name:", data.get("father_name"))
            st.write("Mobile:", data.get("mobile"))

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Approve {doc_id}"):

                    # Generate password
                    raw_password = data.get("mobile")[-4:]
                    hashed = hash_password(raw_password)

                    db.collection("users").add({
                        "name": data.get("name"),
                        "father_name": data.get("father_name"),
                        "mobile": data.get("mobile"),
                        "password_hash": hashed,
                        "role": "Member",
                        "is_approved": True,
                        "is_blocked": False
                    })

                    db.collection("registration_requests").document(doc_id).update({
                        "status": "approved"
                    })

                    st.success(f"Approved. Password is last 4 digits: {raw_password}")
                    st.rerun()

            with col2:
                if st.button(f"Reject {doc_id}"):

                    db.collection("registration_requests").document(doc_id).update({
                        "status": "rejected"
                    })

                    st.warning("Request Rejected")
                    st.rerun()

            st.divider()
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

    st.title("📅 Plan Next Meeting")

    doc = db.collection("admin_settings").document("meeting_options").get()

    if doc.exists:
        data = doc.to_dict()

        meeting_id = data.get("meeting_id")

        agenda_options = data.get("agenda_options", [])
        date_options = data.get("date_options", [])
        time_options = data.get("time_options", [])
        place_options = data.get("place_options", [])

        # Show current meeting ID
        st.info(f"Current Meeting ID: {meeting_id}")

        # ---------------- FORM ----------------
        with st.form("meeting_vote_form"):

            name_father = st.text_input("Your Name & Father Name")

            selected_agenda = st.selectbox("Select Agenda", agenda_options)
            selected_date = st.selectbox("Select Date", date_options)
            selected_time = st.selectbox("Select Time", time_options)
            selected_place = st.selectbox("Select Place", place_options)

            submit_vote = st.form_submit_button("Submit Vote")

            if submit_vote:

                if name_father.strip() == "":
                    st.warning("Please enter your name.")

                else:
                    clean_name = name_father.strip().lower()

                    # Check if already voted in this meeting
                    existing_vote = db.collection("meeting_details") \
                        .where("meeting_id", "==", meeting_id) \
                        .where("name_father", "==", clean_name) \
                        .stream()

                    if list(existing_vote):
                        st.error("You have already voted for this meeting.")

                    else:
                        db.collection("meeting_details").add({
                            "meeting_id": meeting_id,
                            "name_father": clean_name,
                            "agenda": selected_agenda,
                            "date": selected_date,
                            "time": selected_time,
                            "place": selected_place,
                            "voted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })

                        st.success("Vote submitted successfully!")
                        st.rerun()

    else:
        st.error("Meeting options not found.")
                     
        # ---------------- RESULTS ----------------
        st.divider()
        st.subheader("📊 Live Voting Results")

        votes = db.collection("meeting_details").where("meeting_id", "==", meeting_id).stream()

        agenda_count = {}
        date_count = {}
        time_count = {}
        place_count = {}

        vote_list = []
        total_votes = 0

        for vote in votes:
            vote_data = vote.to_dict()
            total_votes += 1

            agenda = vote_data.get("agenda")
            date = vote_data.get("date")
            time = vote_data.get("time")
            place = vote_data.get("place")

            agenda_count[agenda] = agenda_count.get(agenda, 0) + 1
            date_count[date] = date_count.get(date, 0) + 1
            time_count[time] = time_count.get(time, 0) + 1
            place_count[place] = place_count.get(place, 0) + 1

            vote_list.append(vote_data)

        if total_votes > 0:

            def calculate_percent(count_dict):
                return {k: round((v / total_votes) * 100, 2) for k, v in count_dict.items()}

            st.write("### Agenda (%)")
            st.write(calculate_percent(agenda_count))

            st.write("### Date (%)")
            st.write(calculate_percent(date_count))

            st.write("### Time (%)")
            st.write(calculate_percent(time_count))

            st.write("### Place (%)")
            st.write(calculate_percent(place_count))

            # ---------------- TABLE ----------------
            st.divider()
            st.subheader("📋 Submitted Votes")

            import pandas as pd
            df = pd.DataFrame(vote_list)

            st.dataframe(df)

        else:
            st.info("No votes submitted yet.")

        
              
      

        
  


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
            
