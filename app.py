import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import bcrypt

# ---------------- PAGE CONFIG ----------------
# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Volunteer Portal",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>

/* Import Professional Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.main {
    background-color: #f3f6fb;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
}
[data-testid="stSidebar"] * {
    color: #f9fafb !important;
}

/* Container spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Card effect for forms & containers */
div[data-testid="stVerticalBlock"] > div:has(div.stContainer) {
    background-color: white;
    padding: 1.5rem;
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04);
}

/* Buttons */
.stButton>button {
    border-radius: 8px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    border: none;
    background-color: #2563eb;
    color: white;
    transition: all 0.2s ease-in-out;
}

.stButton>button:hover {
    background-color: #1d4ed8;
    transform: translateY(-1px);
}

/* Inputs */
.stTextInput>div>div>input,
.stTextArea textarea,
.stSelectbox>div>div {
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background-color: white;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

/* Success / Warning / Error polish */
.stAlert-success {
    border-radius: 10px;
}

.stAlert-error {
    border-radius: 10px;
}

.stAlert-warning {
    border-radius: 10px;
}

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
# ---------------- SESSION STATE ----------------
# ---------------- SESSION STATE ----------------
default_states = {
    "logged_in": False,
    "role": None,
    "user_id": None,
}

for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------- SIDEBAR ----------------
# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.markdown("## Volunteer Portal")
    st.markdown("---")

    # Initialize menu state
    if "menu" not in st.session_state:
        st.session_state.menu = "Public Notice Board"

    if not st.session_state.logged_in:

        options = ["Public Notice Board", "Login"]

        if st.session_state.menu not in options:
            st.session_state.menu = "Public Notice Board"

        menu = st.radio(
            "Navigation",
            options,
            index=options.index(st.session_state.menu),
            label_visibility="collapsed"
        )

    else:

        main_options = [
            "Dashboard",
            "Teams",
            "Meetings",
            "Plan Next Meeting",
            "Reports",
            "Public Notice Board",
            "Logout"
        ]

        if st.session_state.role == "Admin":
            main_options.append("Admin Panel")

        if st.session_state.menu not in main_options:
            st.session_state.menu = "Dashboard"

        menu = st.radio(
            "Navigation",
            main_options,
            index=main_options.index(st.session_state.menu),
            label_visibility="collapsed"
        )

    # Save selected menu
    st.session_state.menu = menu
# ---------------- PUBLIC NOTICE BOARD ----------------
# ---------------- PUBLIC NOTICE BOARD ----------------
# ---------------- PUBLIC NOTICE BOARD ----------------
if menu == "Public Notice Board":

    st.title("Public Notice Board")
    st.markdown("Stay updated with latest announcements and discussions.")
    st.divider()

    # ================= POST NOTICE =================
    with st.container(border=True):

        st.subheader("Post New Notice")

        if st.session_state.get("logged_in"):
            auto_name = f"{st.session_state.get('name','')} / {st.session_state.get('father_name','')}"
        else:
            auto_name = st.text_input("Your Name")

        notice_text = st.text_area("Write Notice", height=100)

        if st.button("Post Notice", use_container_width=True):
            if notice_text.strip() == "" or auto_name.strip() == "":
                st.warning("Name and notice text are required.")
            else:
                db.collection("notices").add({
                    "notice": notice_text.strip(),
                    "name_father": auto_name,
                    "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "is_pinned": False
                })
                st.success("Notice posted successfully.")
                st.rerun()

    st.divider()

    # ================= FETCH & DISPLAY =================
    notices = db.collection("notices").stream()
    notice_list = []

    for notice_doc in notices:
        data = notice_doc.to_dict()
        data["doc_id"] = notice_doc.id
        notice_list.append(data)

    notice_list = sorted(
        notice_list,
        key=lambda x: (
            x.get("is_pinned", False),
            x.get("posted_at", "")
        ),
        reverse=True
    )

    if not notice_list:
        st.info("No notices available.")
    else:
        for data in notice_list:

            notice_id = data.get("doc_id")
            notice_text = data.get("notice", "")
            name_father = data.get("name_father", "Unknown")
            posted_at = data.get("posted_at", "")
            is_pinned = data.get("is_pinned", False)

            with st.container(border=True):

                header_col1, header_col2 = st.columns([4,1])

                with header_col1:
                    if is_pinned:
                        st.markdown("**Pinned Notice**")
                    st.markdown(f"### {notice_text}")
                    st.caption(f"Posted by {name_father} • {posted_at}")

                with header_col2:
                    if st.button("Pin / Unpin", key=f"pin_{notice_id}"):
                        db.collection("notices").document(notice_id).update({
                            "is_pinned": not is_pinned
                        })
                        st.rerun()

                # -------- ADMIN ACTIONS --------
                if st.session_state.get("role") == "Admin":

                    st.markdown("#### Manage Notice")
                    edit_col1, edit_col2 = st.columns(2)

                    with edit_col1:
                        new_text = st.text_input(
                            "Edit Notice",
                            value=notice_text,
                            key=f"edit_{notice_id}"
                        )
                        if st.button("Save", key=f"save_{notice_id}"):
                            db.collection("notices").document(notice_id).update({
                                "notice": new_text.strip()
                            })
                            st.success("Notice updated.")
                            st.rerun()

                    with edit_col2:
                        if st.button("Delete", key=f"delete_{notice_id}"):
                            db.collection("notices").document(notice_id).delete()
                            st.success("Notice deleted.")
                            st.rerun()

                st.divider()

                # ================= COMMENTS =================
                st.subheader("Comments")

                comments = db.collection("notices") \
                    .document(notice_id) \
                    .collection("comments") \
                    .stream()

                for c in comments:
                    comment_data = c.to_dict()
                    with st.container():
                        st.markdown(f"**{comment_data.get('name_father','User')}**")
                        st.write(comment_data.get("comment",""))
                        st.caption(comment_data.get("commented_at",""))
                        st.markdown("---")

                # -------- ADD COMMENT --------
                if st.session_state.get("logged_in"):
                    comment_name = f"{st.session_state.get('name','')} / {st.session_state.get('father_name','')}"
                else:
                    comment_name = st.text_input("Your Name", key=f"name_{notice_id}")

                comment_text = st.text_input("Add Comment", key=f"comment_{notice_id}")

                if st.button("Submit Comment", key=f"submit_{notice_id}"):

                    if comment_text.strip() == "" or comment_name.strip() == "":
                        st.warning("Name and comment are required.")
                    else:
                        db.collection("notices") \
                            .document(notice_id) \
                            .collection("comments") \
                            .add({
                                "name_father": comment_name,
                                "comment": comment_text.strip(),
                                "commented_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })

                        st.success("Comment added.")
                        st.rerun()

            st.markdown(" ")
# ---------------- LOGIN ----------------
elif menu == "Login":

    st.title("Account Access")
    st.markdown("Login to access your dashboard or submit a registration request.")
    st.divider()

    # ================= LOGIN CARD =================
    with st.container(border=True):

        st.subheader("Login")

        mobile = st.text_input("Mobile Number")
        password = st.text_input("Password", type="password")

        login_clicked = st.button("Login", use_container_width=True)

        if login_clicked:

            user = get_user_by_mobile(mobile.strip())

            if not user:
                st.error("User not found.")

            elif not user.get("is_approved", False):
                st.warning("Account not approved by admin yet.")

            elif user.get("is_blocked", False):
                st.error("Your account is blocked.")

            elif not check_password(password, user.get("password_hash")):
                st.error("Incorrect password.")

            else:
                # Successful login
                st.session_state.logged_in = True
                st.session_state.role = user.get("role")
                st.session_state.user_id = user.get("mobile")
                st.session_state.name = user.get("name")
                st.session_state.father_name = user.get("father_name")

                st.success("Login successful.")
                st.rerun()
    # ================= FORCE PASSWORD CHANGE =================
    if st.session_state.get("force_password_change"):

        st.divider()

        with st.container(border=True):

            st.subheader("Update Password")

            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            if st.button("Update Password", use_container_width=True):

                if len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                    st.stop()

                if new_password != confirm_password:
                    st.error("Passwords do not match.")
                    st.stop()

                hashed_password = hash_password(new_password)

                db.collection("users").document(
                    st.session_state.get("temp_user_id")
                ).update({
                    "password_hash": hashed_password,
                    "must_change_password": False
                })

                st.session_state.force_password_change = False
                st.session_state.temp_user_id = None

                st.success("Password updated successfully. Please login again.")
                st.rerun()

    st.divider()

    # ================= REGISTRATION CARD =================
                  with st.container(border=True):

        st.subheader("New Registration")

        with st.form("registration_form"):

            reg_name = st.text_input("Full Name")
            reg_father = st.text_input("Father Name")
            reg_mobile = st.text_input("Mobile Number (10 digits)")

            reg_submit = st.form_submit_button("Submit Registration")

            if reg_submit:

                reg_name = reg_name.strip()
                reg_father = reg_father.strip()
                reg_mobile = reg_mobile.strip()

                if not reg_name or not reg_father or not reg_mobile:
                    st.warning("All fields are required.")
                    st.stop()

                if not reg_mobile.isdigit() or len(reg_mobile) != 10:
                    st.error("Mobile number must be exactly 10 digits.")
                    st.stop()

                db.collection("registration_requests").add({
                    "name": reg_name,
                    "father_name": reg_father,
                    "mobile": reg_mobile,
                    "status": "pending",
                    "requested_at": datetime.utcnow()
                })

                st.success("Registration submitted successfully.")
                st.rerun()
            # Check existing user
            existing_user = list(
                db.collection("users")
                .where("mobile", "==", reg_mobile)
                .stream()
            )

            if existing_user:
                st.warning("User already registered. Please login.")
                st.stop()

            # Check existing pending request
            existing_request = list(
                db.collection("registration_requests")
                .where("mobile", "==", reg_mobile)
                .stream()
            )

            if existing_request:
                st.warning("Registration already pending approval.")
                st.stop()

            # 🔥 FORCE WRITE
            db.collection("registration_requests").add({
                "name": reg_name,
                "father_name": reg_father,
                "mobile": reg_mobile,
                "status": "pending",
                "requested_at": datetime.utcnow()
            })

        st.success("Registration submitted successfully.")
        st.rerun()

    except Exception as e:
        st.error(f"Registration failed: {e}")
#================= MEETING MANAGEMENT =================#
# ---------------- MEETINGS ----------------
elif menu == "Meetings":

    st.title("Meeting Attendance")

    # ================= LOAD MEETING =================
    try:
        with st.spinner("Loading meeting details..."):
            meeting_ref = db.collection("admin_settings").document("meeting_options")
            meeting_doc = meeting_ref.get()
    except Exception as e:
        st.error(f"Error loading meeting configuration: {e}")
        st.stop()

    if not meeting_doc.exists:
        st.error("Meeting not configured by admin.")
        st.stop()

    meeting_data = meeting_doc.to_dict()
    meeting_id = meeting_data.get("meeting_id")
    meeting_status = meeting_data.get("status", "Closed")

    col1, col2 = st.columns(2)
    col1.info(f"Meeting ID: {meeting_id}")
    col2.info(f"Status: {meeting_status}")

    # ================= STATUS CHECK =================
    if meeting_status != "Active":
        st.warning("Meeting is currently closed. Attendance disabled.")
        st.stop()

    # ================= LOGIN CHECK =================
    if not st.session_state.get("logged_in"):
        st.warning("Please login to submit attendance.")
        st.stop()

    # ================= USER INFO =================
    auto_name = f"{st.session_state.get('name')} / {st.session_state.get('father_name')}"
    user_id = st.session_state.get("user_id")
    clean_name = auto_name.strip().lower()

    st.text_input("Your Name", value=auto_name, disabled=True)

    # ================= ATTENDANCE FORM =================
    with st.form("attendance_form", clear_on_submit=False):

        attending = st.radio("Will You Attend?", ["Yes", "No"])
        reason = st.text_area("Reason (Required if No)")
        submit = st.form_submit_button("Submit Attendance")

    # ================= HANDLE SUBMIT =================
    if submit:

        if attending == "No" and not reason.strip():
            st.warning("Reason is required if not attending.")
            st.stop()

        try:
            with st.spinner("Submitting attendance..."):

                existing = list(
                    db.collection("attendance_details")
                    .where("meeting_id", "==", meeting_id)
                    .where("user_id", "==", user_id)
                    .stream()
                )

                if existing:
                    st.error("You have already submitted attendance.")
                    st.stop()

                db.collection("attendance_details").add({
                    "meeting_id": meeting_id,
                    "name": clean_name,
                    "user_id": user_id,
                    "attending": attending,
                    "reason": reason.strip() if attending == "No" else "",
                    "submitted_at": datetime.utcnow()
                })

            st.success("Attendance recorded successfully.")
            st.rerun()

        except Exception as e:
            st.error(f"Failed to submit attendance: {e}")
# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":

    st.title("Meeting Analytics Dashboard")
    st.markdown("Clear overview of current meeting voting results")
    st.divider()

    # ================= LOAD MEETING =================
    try:
        with st.spinner("Loading meeting data..."):
            doc = db.collection("admin_settings").document("meeting_options").get()
    except Exception as e:
        st.error(f"Error loading meeting settings: {e}")
        st.stop()

    if not doc.exists:
        st.error("Meeting settings not found.")
        st.stop()

    meeting_id = doc.to_dict().get("meeting_id")
    meeting_status = doc.to_dict().get("status", "Closed")

    col1, col2 = st.columns(2)
    col1.info(f"Meeting ID: {meeting_id}")
    col2.info(f"Status: {meeting_status}")

    st.divider()

    # ================= LOAD VOTES =================
    try:
        with st.spinner("Fetching votes..."):
            votes = list(
                db.collection("meeting_details")
                .where("meeting_id", "==", meeting_id)
                .stream()
            )
    except Exception as e:
        st.error(f"Error loading votes: {e}")
        st.stop()

    if not votes:
        st.warning("No votes submitted yet.")
        st.stop()

    agenda_count = {}
    date_count = {}
    time_count = {}
    place_count = {}
    rows = []

    for vote in votes:
        data = vote.to_dict()
        rows.append(data)

        agenda_count[data.get("agenda")] = agenda_count.get(data.get("agenda"), 0) + 1
        date_count[data.get("date")] = date_count.get(data.get("date"), 0) + 1
        time_count[data.get("time")] = time_count.get(data.get("time"), 0) + 1
        place_count[data.get("place")] = place_count.get(data.get("place"), 0) + 1

    total_votes = len(votes)

    st.metric("Total Votes", total_votes)
    st.divider()

    # ================= PIE CHARTS =================
    import matplotlib.pyplot as plt

    def draw_pie(data_dict, title):
        fig, ax = plt.subplots(figsize=(3,3))
        ax.pie(
            data_dict.values(),
            labels=data_dict.keys(),
            autopct="%1.1f%%",
            startangle=90
        )
        ax.set_title(title)
        st.pyplot(fig)

    col1, col2 = st.columns(2)

    with col1:
        draw_pie(agenda_count, "Agenda Distribution")
        draw_pie(date_count, "Date Distribution")

    with col2:
        draw_pie(time_count, "Time Distribution")
        draw_pie(place_count, "Place Distribution")

    st.divider()

    # ================= CLEAN TABLE =================
    st.subheader("Submitted Votes")

    import pandas as pd
    df_table = pd.DataFrame(rows)

    st.dataframe(
        df_table,
        use_container_width=True,
        height=400
    )
# ---------------- TEAMS ----------------
elif menu == "Teams":

    st.title("👥 Team Dashboard")

    selected_team = st.selectbox(
        "Select Team",
        ["Jury Team", "Task Team", "Monitoring Team", "Data Team"]
    )

    # ================= AUTO NAME =================
    if st.session_state.get("logged_in"):

        auto_name = f"{st.session_state.name} / {st.session_state.father_name}"

        name = st.text_input(
            "Member Name",
            value=auto_name,
            disabled=True
        )

    else:
        name = st.text_input("Member Name")

    # ================= FORM =================
    with st.form("team_form"):

        details = st.text_area("Details / Work Description")

        submit = st.form_submit_button("Save")

        if submit:

            if name.strip() == "":
                st.warning("Member name is required.")

            elif details.strip() == "":
                st.warning("Details are required.")

            else:

                db.collection("teams").add({
                    "team": selected_team,
                    "name": name.strip().lower(),
                    "user_id": st.session_state.get("user_id", "public"),
                    "details": details.strip(),
                    "created_by_role": st.session_state.get("role"),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

                st.success("Saved Successfully")
                st.rerun()

    # ================= RECORDS =================
    st.divider()
    st.subheader("Team Records")

    records = db.collection("teams").where(
        "team", "==", selected_team
    ).stream()

    for r in records:
        data = r.to_dict()
        st.write(f"👤 {data.get('name')} — {data.get('details')}")
# ---------------- MEETINGS ----------------
# ---------------- MEETINGS ----------------
elif menu == "Meetings":

    st.title("Meeting Attendance")

    # 🔍 Get current meeting
    meeting_ref = db.collection("admin_settings").document("meeting_options")
    meeting_doc = meeting_ref.get()

    if not meeting_doc.exists:
        st.error("No meeting configured by admin.")
        st.stop()

    meeting_data = meeting_doc.to_dict()
    meeting_id = meeting_data.get("meeting_id")
    meeting_status = meeting_data.get("status", "Closed")

    st.info(f"Meeting ID: {meeting_id}")
    st.info(f"Status: {meeting_status}")

    st.divider()

    # 🚫 Block attendance if closed
    if meeting_status != "Active":
        st.warning("Meeting is closed. Attendance disabled.")
        st.stop()

    # ================= ATTENDANCE =================
    if not st.session_state.get("logged_in"):
        st.info("Login required to submit attendance.")
        st.stop()

    auto_name = f"{st.session_state.get('name')} / {st.session_state.get('father_name')}"
    user_id = st.session_state.get("user_id")
    clean_name = auto_name.strip().lower()

    st.text_input("Your Name", value=auto_name, disabled=True)

    with st.form("attendance_form"):

        attending = st.radio("Will You Attend?", ["Yes", "No"])
        reason = st.text_area("Reason (Required if No)")
        submit = st.form_submit_button("Submit Attendance")

        if submit:

            if attending == "No" and not reason.strip():
                st.warning("Reason is required if not attending.")
                st.stop()

            existing = db.collection("attendance_details") \
                .where("meeting_id", "==", meeting_id) \
                .where("user_id", "==", user_id) \
                .stream()

            if list(existing):
                st.error("Attendance already submitted.")
                st.stop()

            db.collection("attendance_details").add({
                "meeting_id": meeting_id,
                "name": clean_name,
                "user_id": user_id,
                "attending": attending,
                "reason": reason.strip() if attending == "No" else "",
                "submitted_at": datetime.utcnow()
            })

            st.success("Attendance recorded successfully.")
            st.rerun()
# ---------------- PLAN NEXT MEETING ----------------
# ---------------- PLAN NEXT MEETING ----------------
elif menu == "Plan Next Meeting":

    st.title("Vote for Next Meeting")

    meeting_ref = db.collection("admin_settings").document("meeting_options")
    meeting_doc = meeting_ref.get()

    if not meeting_doc.exists:
        st.error("Meeting not configured by admin.")
        st.stop()

    meeting_data = meeting_doc.to_dict()

    meeting_id = meeting_data.get("meeting_id")
    meeting_status = meeting_data.get("status", "Closed")

    agenda_options = meeting_data.get("agenda_options", [])
    date_options = meeting_data.get("date_options", [])
    time_options = meeting_data.get("time_options", [])
    place_options = meeting_data.get("place_options", [])

    st.info(f"Meeting ID: {meeting_id}")
    st.info(f"Status: {meeting_status}")

    if meeting_status != "Active":
        st.warning("Voting is closed.")
        st.stop()

    if not st.session_state.get("logged_in"):
        st.warning("Login required to vote.")
        st.stop()

    auto_name = f"{st.session_state.get('name')} / {st.session_state.get('father_name')}"
    user_id = st.session_state.get("user_id")
    clean_name = auto_name.strip().lower()

    st.text_input("Your Name", value=auto_name, disabled=True)

    with st.form("vote_form"):

        selected_agenda = st.selectbox("Select Agenda", agenda_options)
        selected_date = st.selectbox("Select Date", date_options)
        selected_time = st.selectbox("Select Time", time_options)
        selected_place = st.selectbox("Select Place", place_options)

        submit_vote = st.form_submit_button("Submit Vote")

        if submit_vote:

            existing_vote = db.collection("meeting_details") \
                .where("meeting_id", "==", meeting_id) \
                .where("user_id", "==", user_id) \
                .stream()

            if list(existing_vote):
                st.error("You have already voted.")
                st.stop()

            db.collection("meeting_details").add({
                "meeting_id": meeting_id,
                "name_father": clean_name,
                "user_id": user_id,
                "agenda": selected_agenda,
                "date": selected_date,
                "time": selected_time,
                "place": selected_place,
                "voted_at": datetime.utcnow()
            })

            st.success("Vote submitted successfully.")
            st.rerun()
        #---reports---#
#------#-----#
elif menu == "Reports":

    st.title("📊 Reports")

    if not st.session_state.get("logged_in"):
        st.warning("Login required.")
        st.stop()

    user_id = st.session_state.get("user_id")
    user_name = f"{st.session_state.get('name')} / {st.session_state.get('father_name')}"
    role = st.session_state.get("role")

    tab1, tab2 = st.tabs(["📌 Complaints", "💡 Suggestions"])

    # ======================================================
    # ===================== COMPLAINTS ======================
    # ======================================================

    with tab1:

        st.subheader("Submit Complaint")

        with st.form("complaint_form"):
            complaint_text = st.text_area("Write Complaint")
            submit = st.form_submit_button("Submit")

        if submit:

            clean_text = complaint_text.strip().lower()

            if clean_text == "":
                st.warning("Complaint cannot be empty.")
                st.stop()

            # ✅ Prevent same complaint by same user
            duplicate_check = db.collection("complaints") \
                .where("created_by", "==", user_id) \
                .where("complaint", "==", clean_text) \
                .stream()

            if list(duplicate_check):
                st.error("You have already submitted this same complaint.")
                st.stop()

            db.collection("complaints").add({
                "complaint": clean_text,
                "created_by": user_id,
                "created_name": user_name,
                "created_at": datetime.utcnow(),
                "likes": 0,
                "is_published": False
            })

            st.success("Complaint submitted.")
            st.rerun()

        st.divider()
        st.subheader("All Complaints")

        complaints = db.collection("complaints").stream()
        complaint_list = []

        for c in complaints:
            data = c.to_dict()
            data["doc_id"] = c.id
            complaint_list.append(data)

        complaint_list = sorted(
            complaint_list,
            key=lambda x: x.get("likes", 0),
            reverse=True
        )

        for comp in complaint_list:

            doc_id = comp["doc_id"]
            text = comp.get("complaint")
            likes = comp.get("likes", 0)
            is_published = comp.get("is_published", False)
            creator_name = comp.get("created_name")

            if is_published:
                st.markdown("### ✅ Published Complaint")

            st.markdown(f"### 📝 {text}")
            st.markdown(f"👍 Likes: **{likes}**")

            if is_published:
                st.caption(f"👤 Complainer: {creator_name}")

            # -------- LIKE --------
            if comp.get("created_by") != user_id:

                existing_like = db.collection("complaints") \
                    .document(doc_id) \
                    .collection("likes") \
                    .where("user_id", "==", user_id) \
                    .stream()

                if not list(existing_like):

                    if st.button("👍 Like", key=f"like_{doc_id}"):

                        db.collection("complaints") \
                            .document(doc_id) \
                            .collection("likes") \
                            .add({
                                "user_id": user_id,
                                "name": user_name,
                                "liked_at": datetime.utcnow()
                            })

                        db.collection("complaints") \
                            .document(doc_id) \
                            .update({
                                "likes": likes + 1
                            })

                        st.rerun()
                else:
                    st.success("You liked this.")

            # -------- Likes Table --------
            st.markdown("##### 👍 Liked By")

            likes_docs = db.collection("complaints") \
                .document(doc_id) \
                .collection("likes") \
                .stream()

            like_data = [l.to_dict() for l in likes_docs]

            if like_data:
                df_likes = pd.DataFrame(like_data)
                st.dataframe(df_likes[["name", "liked_at"]], use_container_width=True)
            else:
                st.info("No likes yet.")

            # -------- ADMIN PUBLISH --------
            if role == "Admin":

                if not is_published:
                    if st.button("🚀 Publish", key=f"publish_{doc_id}"):

                        db.collection("complaints") \
                            .document(doc_id) \
                            .update({"is_published": True})

                        st.success("Complaint Published.")
                        st.rerun()
                else:
                    if st.button("❌ Unpublish", key=f"unpublish_{doc_id}"):

                        db.collection("complaints") \
                            .document(doc_id) \
                            .update({"is_published": False})

                        st.warning("Complaint Hidden.")
                        st.rerun()

            st.divider()

    # ======================================================
    # ==================== SUGGESTIONS =====================
    # ======================================================

    with tab2:

        st.subheader("Submit Suggestion")

        with st.form("suggestion_form"):
            suggestion_text = st.text_area("Write Suggestion")
            submit = st.form_submit_button("Submit")

        if submit:

            clean_text = suggestion_text.strip().lower()

            if clean_text == "":
                st.warning("Suggestion cannot be empty.")
                st.stop()

            # ✅ Prevent same suggestion by same user
            duplicate_check = db.collection("suggestions") \
                .where("created_by", "==", user_id) \
                .where("suggestion", "==", clean_text) \
                .stream()

            if list(duplicate_check):
                st.error("You have already submitted this same suggestion.")
                st.stop()

            db.collection("suggestions").add({
                "suggestion": clean_text,
                "created_by": user_id,
                "created_name": user_name,
                "created_at": datetime.utcnow(),
                "likes": 0
            })

            st.success("Suggestion submitted.")
            st.rerun()

        st.divider()
        st.subheader("All Suggestions")

        suggestions = db.collection("suggestions").stream()
        suggestion_list = []

        for s in suggestions:
            data = s.to_dict()
            data["doc_id"] = s.id
            suggestion_list.append(data)

        suggestion_list = sorted(
            suggestion_list,
            key=lambda x: x.get("likes", 0),
            reverse=True
        )

        for sug in suggestion_list:

            doc_id = sug["doc_id"]
            text = sug.get("suggestion")
            likes = sug.get("likes", 0)
            creator_name = sug.get("created_name")

            st.markdown(f"### 💡 {text}")
            st.markdown(f"👍 Likes: **{likes}**")
            st.caption(f"👤 Suggested by: {creator_name}")

            if sug.get("created_by") != user_id:

                existing_like = db.collection("suggestions") \
                    .document(doc_id) \
                    .collection("likes") \
                    .where("user_id", "==", user_id) \
                    .stream()

                if not list(existing_like):

                    if st.button("👍 Like", key=f"sug_like_{doc_id}"):

                        db.collection("suggestions") \
                            .document(doc_id) \
                            .collection("likes") \
                            .add({
                                "user_id": user_id,
                                "name": user_name,
                                "liked_at": datetime.utcnow()
                            })

                        db.collection("suggestions") \
                            .document(doc_id) \
                            .update({
                                "likes": likes + 1
                            })

                        st.rerun()
                else:
                    st.success("You liked this.")

            # -------- Likes Table --------
            st.markdown("##### 👍 Liked By")

            likes_docs = db.collection("suggestions") \
                .document(doc_id) \
                .collection("likes") \
                .stream()

            like_data = [l.to_dict() for l in likes_docs]

            if like_data:
                df_likes = pd.DataFrame(like_data)
                st.dataframe(df_likes[["name", "liked_at"]], use_container_width=True)
            else:
                st.info("No likes yet.")

            st.divider()
#------admin panel-----#
#-------a--------------#
# ================= ADMIN PANEL =================
elif menu == "Admin Panel":

    # 🔒 Security Check
    if st.session_state.get("role") != "Admin":
        st.error("Access Denied")
        st.stop()

    st.title("Admin Control Center")

    # ======================================================
    # REGISTRATION REQUESTS
    # ======================================================

    st.subheader("Pending Registration Requests")

    with st.spinner("Fetching registration requests..."):
        requests = list(db.collection("registration_requests").stream())

    if not requests:
        st.info("No pending requests.")
    else:
        for req in requests:

            data = req.to_dict()
            req_id = req.id
            name = data.get("name")
            father_name = data.get("father_name")
            mobile = data.get("mobile")

            st.markdown(f"### {name} / {father_name}")
            st.caption(f"Mobile: {mobile}")

            col1, col2 = st.columns(2)

            # APPROVE
      if st.button("Force Test Registration Write"):
    db.collection("registration_requests").add({
        "name": "Test User",
        "father_name": "Test Father",
        "mobile": "9999999999",
        "status": "pending",
        "requested_at": datetime.utcnow()
    })
    st.success("Test registration created")
            # REJECT
            with col2:
                if st.button("Reject", key=f"reject_{req_id}"):

                    try:
                        with st.spinner("Rejecting request..."):
                            db.collection("registration_requests").document(req_id).delete()

                        st.warning("Request rejected.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Rejection failed: {e}")

            st.divider()

    # ======================================================
    # USER MANAGEMENT
    # ======================================================

    st.subheader("Registered Users")

    with st.spinner("Loading users..."):
        users = list(db.collection("users").stream())

    if not users:
        st.info("No users found.")
    else:
        for user_doc in users:

            user_data = user_doc.to_dict()
            user_id = user_doc.id
            name = user_data.get("name")
            father_name = user_data.get("father_name")
            mobile = user_data.get("mobile")
            is_blocked = user_data.get("is_blocked", False)

            status = "🔴 Blocked" if is_blocked else "🟢 Active"

            st.markdown(f"### {name} / {father_name}")
            st.caption(f"Mobile: {mobile}")
            st.write(f"Status: {status}")

            if st.button(
                "Unblock User" if is_blocked else "Block User",
                key=f"block_{user_id}"
            ):
                try:
                    with st.spinner("Updating user status..."):
                        db.collection("users").document(user_id).update({
                            "is_blocked": not is_blocked
                        })

                    st.success("User status updated successfully.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Status update failed: {e}")

            st.divider()

    # ======================================================
    # MEETING MANAGEMENT
    # ======================================================

    st.subheader("Meeting Management")

    meeting_ref = db.collection("admin_settings").document("meeting_options")

    try:
        meeting_doc = meeting_ref.get()
        meeting_data = meeting_doc.to_dict() if meeting_doc.exists else {}
    except Exception as e:
        st.error(f"Error loading meeting settings: {e}")
        st.stop()

    current_meeting_id = meeting_data.get("meeting_id", "Not Set")
    current_status = meeting_data.get("status", "Closed")

    col1, col2 = st.columns(2)
    col1.info(f"Meeting ID: {current_meeting_id}")
    col2.info(f"Status: {current_status}")

    st.divider()

    # CREATE / ACTIVATE MEETING
    with st.form("create_meeting_form"):

        new_meeting_id = st.text_input("Meeting ID")
        agenda_input = st.text_area("Agenda Options (comma separated)")
        date_input = st.text_area("Date Options (comma separated)")
        time_input = st.text_area("Time Options (comma separated)")
        place_input = st.text_area("Place Options (comma separated)")

        activate = st.form_submit_button("Activate Meeting")

        if activate:
            if not new_meeting_id.strip():
                st.error("Meeting ID required.")
            else:
                try:
                    with st.spinner("Activating meeting..."):

                        meeting_ref.set({
                            "meeting_id": new_meeting_id.strip(),
                            "agenda_options": [x.strip() for x in agenda_input.split(",") if x.strip()],
                            "date_options": [x.strip() for x in date_input.split(",") if x.strip()],
                            "time_options": [x.strip() for x in time_input.split(",") if x.strip()],
                            "place_options": [x.strip() for x in place_input.split(",") if x.strip()],
                            "status": "Active",
                            "created_at": datetime.utcnow()
                        })

                    st.success("Meeting activated successfully.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Meeting activation failed: {e}")

    # CLOSE MEETING
    if current_status == "Active":

        st.divider()

        if st.button("Close Meeting"):
            try:
                with st.spinner("Closing meeting..."):
                    meeting_ref.update({
                        "status": "Closed"
                    })

                st.success("Meeting closed successfully.")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to close meeting: {e}")
    if st.button("🔥 Force Registration Write Test"):
    db.collection("registration_requests").add({
        "name": "Debug User",
        "father_name": "Debug Father",
        "mobile": "9999999999",
        "status": "pending",
        "requested_at": datetime.utcnow()
    })
    st.success("Test registration created.")
