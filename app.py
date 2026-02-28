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

            # ✅ SESSION SET
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user_id = user["id"]

            # 🔥 AUTO NAME STORE (IMPORTANT)
            st.session_state.name = user.get("name")
            st.session_state.father_name = user.get("father_name")

            st.success("Login Successful")
            st.rerun()

        else:
            st.error("Wrong Password")

    st.divider()

    # ---------------- REGISTRATION ----------------
    st.subheader("📝 New Registration")

    with st.form("registration_form"):

        reg_name = st.text_input("Full Name")
        reg_father = st.text_input("Father Name")
        reg_mobile = st.text_input("Mobile Number")

        reg_submit = st.form_submit_button("Submit Registration")

        if reg_submit:

            if reg_name.strip() == "" or reg_father.strip() == "" or reg_mobile.strip() == "":
                st.warning("All fields are required.")

            else:
                existing_user = db.collection("users").where(
                    "mobile", "==", reg_mobile
                ).stream()

                if list(existing_user):
                    st.warning("User already registered. Please login.")

                else:
                    existing_request = db.collection("registration_requests").where(
                        "mobile", "==", reg_mobile
                    ).stream()

                    if list(existing_request):
                        st.warning("Registration already pending.")

                    else:
                        db.collection("registration_requests").add({
                            "name": reg_name.strip(),
                            "father_name": reg_father.strip(),
                            "mobile": reg_mobile.strip(),
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

        st.title("👑 Admin Panel")

        # ================= MEETING MANAGEMENT =================
        st.subheader("📅 Meeting Management")

        meeting_doc = db.collection("admin_settings").document("meeting_options").get()
        meeting_data = meeting_doc.to_dict() if meeting_doc.exists else {}

        current_meeting_id = meeting_data.get("meeting_id", "Not Set")
        current_status = meeting_data.get("status", "Closed")

        st.info(f"Current Meeting ID: {current_meeting_id}")
        st.info(f"Status: {current_status}")

        st.divider()
        st.subheader("Create / Update Active Meeting")

        new_meeting_id = st.text_input("Meeting ID")
        agenda_input = st.text_area("Agenda Options (comma separated)")
        date_input = st.text_area("Date Options (comma separated)")
        time_input = st.text_area("Time Options (comma separated)")
        place_input = st.text_area("Place Options (comma separated)")

        # ---------------- SAVE MEETING ----------------
        if st.button("Save Meeting"):

            if new_meeting_id.strip() == "":
                st.error("Meeting ID is required.")
            else:

                db.collection("admin_settings").document("meeting_options").set({
                    "meeting_id": new_meeting_id.strip(),
                    "agenda_options": [x.strip() for x in agenda_input.split(",") if x.strip()],
                    "date_options": [x.strip() for x in date_input.split(",") if x.strip()],
                    "time_options": [x.strip() for x in time_input.split(",") if x.strip()],
                    "place_options": [x.strip() for x in place_input.split(",") if x.strip()],
                    "status": "Active"
                })

                st.success("Meeting saved and activated.")
                st.rerun()

        # ---------------- CLOSE MEETING ----------------
        if current_status == "Active":

            if st.button("Close Current Meeting"):

                meeting_id = current_meeting_id

                votes = db.collection("meeting_details").where(
                    "meeting_id", "==", meeting_id
                ).stream()

                agenda_count = {}
                date_count = {}
                time_count = {}
                place_count = {}
                total_votes = 0

                for vote in votes:
                    data = vote.to_dict()
                    total_votes += 1

                    agenda = data.get("agenda")
                    date = data.get("date")
                    time = data.get("time")
                    place = data.get("place")

                    agenda_count[agenda] = agenda_count.get(agenda, 0) + 1
                    date_count[date] = date_count.get(date, 0) + 1
                    time_count[time] = time_count.get(time, 0) + 1
                    place_count[place] = place_count.get(place, 0) + 1

                if total_votes == 0:
                    st.error("No votes to finalize.")
                else:

                    winning_agenda = max(agenda_count, key=agenda_count.get)
                    winning_date = max(date_count, key=date_count.get)
                    winning_time = max(time_count, key=time_count.get)
                    winning_place = max(place_count, key=place_count.get)

                    db.collection("meeting_results").document(meeting_id).set({
                        "meeting_id": meeting_id,
                        "total_votes": total_votes,
                        "winning_agenda": winning_agenda,
                        "winning_date": winning_date,
                        "winning_time": winning_time,
                        "winning_place": winning_place,
                        "finalized_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

                    db.collection("admin_settings").document("meeting_options").update({
                        "status": "Closed"
                    })

                    st.success("Meeting finalized and closed.")
                    st.rerun()
# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":

    st.title("📊 Meeting Dashboard")

    doc = db.collection("admin_settings").document("meeting_options").get()

    if doc.exists:

        meeting_id = doc.to_dict().get("meeting_id")
        st.info(f"Active Meeting ID: {meeting_id}")

        votes = db.collection("meeting_details") \
            .where("meeting_id", "==", meeting_id) \
            .stream()

        agenda_count = {}
        date_count = {}
        time_count = {}
        place_count = {}

        rows = []
        total_votes = 0

        for vote in votes:
            data = vote.to_dict()
            total_votes += 1

            agenda = data.get("agenda")
            date = data.get("date")
            time = data.get("time")
            place = data.get("place")
            name = data.get("name_father")

            rows.append(data)

            agenda_count[agenda] = agenda_count.get(agenda, 0) + 1
            date_count[date] = date_count.get(date, 0) + 1
            time_count[time] = time_count.get(time, 0) + 1
            place_count[place] = place_count.get(place, 0) + 1

        if total_votes > 0:

            st.metric("Total Votes", total_votes)

            import pandas as pd

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Agenda %")
                df_agenda = pd.DataFrame(
                    {k: round((v/total_votes)*100,2) for k,v in agenda_count.items()},
                    index=["%"]
                ).T
                st.bar_chart(df_agenda, height=250)

                st.subheader("Date %")
                df_date = pd.DataFrame(
                    {k: round((v/total_votes)*100,2) for k,v in date_count.items()},
                    index=["%"]
                ).T
                st.bar_chart(df_date, height=250)

            with col2:
                st.subheader("Time %")
                df_time = pd.DataFrame(
                    {k: round((v/total_votes)*100,2) for k,v in time_count.items()},
                    index=["%"]
                ).T
                st.bar_chart(df_time, height=250)

                st.subheader("Place %")
                df_place = pd.DataFrame(
                    {k: round((v/total_votes)*100,2) for k,v in place_count.items()},
                    index=["%"]
                ).T
                st.bar_chart(df_place, height=250)

            st.divider()
            st.subheader("🗂 All Submitted Votes")

            df_table = pd.DataFrame(rows)
            st.dataframe(df_table, use_container_width=True)

        else:
            st.warning("No votes submitted yet.")

    else:
        st.error("Meeting settings not found.")
        
                
       
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

    # ================= NAME AUTO FILL =================
    if st.session_state.get("logged_in"):

        auto_name = f"{st.session_state.name} / {st.session_state.father_name}"

        name = st.text_input(
            "Your Name",
            value=auto_name,
            disabled=True
        )

    else:
        name = st.text_input("Your Name")

    # ================= FORM =================
    with st.form("attendance_form"):

        attending = st.radio("Will You Attend?", ["Yes", "No"])
        reason = st.text_area("Reason (if No)")

        submit = st.form_submit_button("Submit")

        if submit:

            if name.strip() == "":
                st.warning("Name is required.")

            elif attending == "No" and reason.strip() == "":
                st.warning("Please provide a reason if not attending.")

            else:

                db.collection("meetings").add({
                    "name": name.strip().lower(),
                    "user_id": st.session_state.get("user_id", "public"),
                    "attending": attending,
                    "reason": reason.strip(),
                    "role": st.session_state.get("role"),
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

                st.success("Attendance Recorded")
                st.rerun()

# ---------------- PLAN NEXT MEETING ----------------
elif menu == "Plan Next Meeting":

    st.title("📅 Plan Next Meeting")

    doc = db.collection("admin_settings").document("meeting_options").get()

    if not doc.exists:
        st.error("Meeting options not found.")
        st.stop()

    data = doc.to_dict()

    meeting_id = data.get("meeting_id")
    agenda_options = data.get("agenda_options", [])
    date_options = data.get("date_options", [])
    time_options = data.get("time_options", [])
    place_options = data.get("place_options", [])

    st.info(f"Current Meeting ID: {meeting_id}")

    # ================= NAME AUTO FILL LOGIC =================
    if st.session_state.get("logged_in"):

        auto_name = f"{st.session_state.name} / {st.session_state.father_name}"

        name_father = st.text_input(
            "Your Name & Father Name",
            value=auto_name,
            disabled=True
        )

        clean_name = auto_name.lower()

    else:

        name_father = st.text_input("Your Name & Father Name")
        clean_name = name_father.strip().lower()

    # ================= VOTING FORM =================
    with st.form("meeting_vote_form"):

        selected_agenda = st.selectbox("Select Agenda", agenda_options)
        selected_date = st.selectbox("Select Date", date_options)
        selected_time = st.selectbox("Select Time", time_options)
        selected_place = st.selectbox("Select Place", place_options)

        submit_vote = st.form_submit_button("Submit Vote")

        if submit_vote:

            if clean_name == "":
                st.warning("Please enter your name.")
            else:

                # Duplicate vote check
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
                        "user_id": st.session_state.get("user_id", "public"),
                        "agenda": selected_agenda,
                        "date": selected_date,
                        "time": selected_time,
                        "place": selected_place,
                        "voted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

                    st.success("Vote submitted successfully!")
                    st.rerun()

    # ================= LIVE RESULTS =================
    st.divider()
    st.subheader("📊 Live Voting Results")

    votes = db.collection("meeting_details") \
        .where("meeting_id", "==", meeting_id) \
        .stream()

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
            return {
                k: round((v / total_votes) * 100, 2)
                for k, v in count_dict.items()
            }

        st.write("### Agenda (%)")
        st.write(calculate_percent(agenda_count))

        st.write("### Date (%)")
        st.write(calculate_percent(date_count))

        st.write("### Time (%)")
        st.write(calculate_percent(time_count))

        st.write("### Place (%)")
        st.write(calculate_percent(place_count))

        # -------- TABLE --------
        st.divider()
        st.subheader("📋 Submitted Votes")

        import pandas as pd
        df = pd.DataFrame(vote_list)
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No votes submitted yet.")
            
