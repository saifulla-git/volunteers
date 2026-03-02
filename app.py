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

# ---------------- GLOBAL PROFESSIONAL THEME ----------------
st.markdown("""
<style>

/* Main background */
.main {
    background-color: #f8fafc;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #111827;
}
[data-testid="stSidebar"] * {
    color: white !important;
    font-size: 15px;
}

/* Reduce top padding */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Buttons */
.stButton>button {
    border-radius: 10px;
    padding: 0.4rem 1rem;
    font-weight: 600;
}

/* Inputs */
.stTextInput>div>div>input,
.stTextArea textarea {
    border-radius: 8px;
}

/* Metrics */
[data-testid="metric-container"] {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
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
with st.sidebar:

    st.markdown("## Volunteer Portal")
    st.markdown("---")

    if not st.session_state.logged_in:

        menu = st.radio(
            "Navigation",
            ["Public Notice Board", "Login"],
            label_visibility="collapsed"
        )

    else:

        st.markdown("### Main")
        menu = st.radio(
            "",
            [
                "Dashboard",
                "Teams",
                "Meetings",
                "Plan Next Meeting",
                "Reports",
                "Public Notice Board",
                "Logout"
            ],
            label_visibility="collapsed"
        )

        # Admin section separated visually
        if st.session_state.role == "Admin":
            st.markdown("---")
            st.markdown("### Administration")
            if st.button("Admin Panel"):
                menu = "Admin Panel"
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

        if st.button("Login", use_container_width=True):

            user = get_user_by_mobile(mobile.strip())

            if not user:
                st.error("User not found.")

            elif not user.get("is_approved", False):
                st.warning("Account not approved by admin yet.")

            elif user.get("is_blocked", False):
                st.error("Your account is blocked.")

            elif check_password(password, user.get("password_hash")):

                if user.get("must_change_password", False):
                    st.session_state.force_password_change = True
                    st.session_state.temp_user_id = user.get("id")
                    st.warning("Password change required.")
                    st.rerun()

                else:
                    st.session_state.logged_in = True
                    st.session_state.role = user.get("role")
                    st.session_state.user_id = user.get("id")
                    st.session_state.name = user.get("name")
                    st.session_state.father_name = user.get("father_name")

                    st.success("Login successful.")
                    st.rerun()

            else:
                st.error("Incorrect password.")

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

                existing_user = db.collection("users") \
                    .where("mobile", "==", reg_mobile) \
                    .stream()

                if list(existing_user):
                    st.warning("User already registered. Please login.")
                    st.stop()

                existing_request = db.collection("registration_requests") \
                    .where("mobile", "==", reg_mobile) \
                    .stream()

                if list(existing_request):
                    st.warning("Registration already pending approval.")
                    st.stop()

                db.collection("registration_requests").add({
                    "name": reg_name,
                    "father_name": reg_father,
                    "mobile": reg_mobile,
                    "status": "pending",
                    "requested_at": datetime.utcnow()
                })

                st.success("Registration submitted. Await admin approval.")
                st.rerun()
#================= MEETING MANAGEMENT =================#

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
elif menu == "Meetings":

    st.title("📅 Meeting Attendance")

    # 🔍 Get current meeting
    doc = db.collection("admin_settings").document("meeting_options").get()

    if not doc.exists:
        st.error("No active meeting found.")
        st.stop()

    data = doc.to_dict()
    meeting_id = data.get("meeting_id")
    meeting_status = data.get("status", "Closed")

    st.info(f"Current Meeting ID: {meeting_id}")
    st.info(f"Status: {meeting_status}")

    # 🚫 Block attendance if meeting closed
    if meeting_status != "Active":
        st.warning("Meeting is closed. Attendance disabled.")
        st.stop()

    # ================= NAME AUTO FILL =================
    if st.session_state.get("logged_in"):

        auto_name = f"{st.session_state.name} / {st.session_state.father_name}"
        user_id = st.session_state.get("user_id")

        st.text_input(
            "Your Name",
            value=auto_name,
            disabled=True
        )

        clean_name = auto_name.lower()

    else:
        user_id = "public"
        name_input = st.text_input("Your Name")
        clean_name = name_input.strip().lower()

    # ================= FORM =================
    with st.form("attendance_form"):

        attending = st.radio("Will You Attend?", ["Yes", "No"])
        reason = st.text_area("Reason (if No)")

        submit = st.form_submit_button("Submit")

        if submit:

            if clean_name == "":
                st.warning("Name is required.")

            elif attending == "No" and reason.strip() == "":
                st.warning("Please provide a reason if not attending.")

            else:

                # ✅ Duplicate attendance check
                if user_id != "public":
                    existing = db.collection("attendance_details") \
                        .where("meeting_id", "==", meeting_id) \
                        .where("user_id", "==", user_id) \
                        .stream()
                else:
                    existing = db.collection("attendance_details") \
                        .where("meeting_id", "==", meeting_id) \
                        .where("name", "==", clean_name) \
                        .stream()

                if list(existing):
                    st.error("You have already submitted attendance.")
                else:

                    db.collection("attendance_details").add({
                        "meeting_id": meeting_id,
                        "name": clean_name,
                        "user_id": user_id,
                        "attending": attending,
                        "reason": reason.strip(),
                        "role": st.session_state.get("role"),
                        "submitted_at": datetime.now()
                    })

                    st.success("Attendance Recorded Successfully.")
                    st.rerun()
# ---------------- PLAN NEXT MEETING ----------------
elif menu == "Plan Next Meeting":

    st.title("📅 Plan Next Meeting")

    doc = db.collection("admin_settings").document("meeting_options").get()

    if not doc.exists:
        st.error("No active meeting found.")
        st.stop()

    data = doc.to_dict()

    meeting_id = data.get("meeting_id")
    meeting_status = data.get("status", "Closed")

    agenda_options = data.get("agenda_options", [])
    date_options = data.get("date_options", [])
    time_options = data.get("time_options", [])
    place_options = data.get("place_options", [])

    st.info(f"Current Meeting ID: {meeting_id}")
    st.info(f"Status: {meeting_status}")

    # 🚫 Block voting if meeting closed
    if meeting_status != "Active":
        st.warning("Meeting is closed. Voting is disabled.")
        st.stop()

    # ================= NAME AUTO FETCH =================
    if st.session_state.get("logged_in"):

        auto_name = f"{st.session_state.name} / {st.session_state.father_name}"
        user_id = st.session_state.get("user_id")

        st.text_input(
            "Your Name & Father Name",
            value=auto_name,
            disabled=True
        )

        clean_name = auto_name.lower()

    else:
        user_id = "public"
        name_input = st.text_input("Your Name & Father Name")
        clean_name = name_input.strip().lower()

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

                # ✅ Logged user duplicate check by user_id
                if user_id != "public":
                    existing_vote = db.collection("meeting_details") \
                        .where("meeting_id", "==", meeting_id) \
                        .where("user_id", "==", user_id) \
                        .stream()
                else:
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
                        "user_id": user_id,
                        "agenda": selected_agenda,
                        "date": selected_date,
                        "time": selected_time,
                        "place": selected_place,
                        "voted_at": datetime.now()
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

        col1, col2 = st.columns(2)

        with col1:
            st.write("### Agenda (%)")
            st.write(calculate_percent(agenda_count))

            st.write("### Date (%)")
            st.write(calculate_percent(date_count))

        with col2:
            st.write("### Time (%)")
            st.write(calculate_percent(time_count))

            st.write("### Place (%)")
            st.write(calculate_percent(place_count))

        st.divider()
        st.subheader("📋 Submitted Votes")

        import pandas as pd
        df = pd.DataFrame(vote_list)
        st.dataframe(df, use_container_width=True)

    else:
        st.info("No votes submitted yet.")
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
elif menu == "Admin Panel":

    if st.session_state.get("role") != "Admin":
        st.error("⛔ Access Denied")
        st.stop()

    st.title("Admin Panel")

    # ================= REGISTRATION REQUESTS =================
    st.subheader("Registration Requests")

    requests = list(db.collection("registration_requests").stream())

    if not requests:
        st.info("No pending registration requests.")
    else:
        for req in requests:

            data = req.to_dict()
            req_id = req.id
            name = data.get("name")
            father_name = data.get("father_name")
            mobile = data.get("mobile")

            if not mobile:
                continue

            existing_user = list(
                db.collection("users")
                .where("mobile", "==", mobile)
                .stream()
            )

            if existing_user:
                db.collection("registration_requests").document(req_id).delete()
                continue

            st.markdown(f"### {name} / {father_name}")
            st.write(f"Mobile: {mobile}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Approve", key=f"approve_{req_id}"):

                    username = mobile
                    plain_password = mobile[-4:]
                    hashed_password = hash_password(plain_password)

                    db.collection("users").document(username).set({
                        "name": name,
                        "father_name": father_name,
                        "mobile": mobile,
                        "role": "Member",
                        "password_hash": hashed_password,
                        "is_approved": True,
                        "is_blocked": False,
                        "created_at": datetime.utcnow()
                    })

                    db.collection("registration_requests").document(req_id).delete()
                    st.success("User Approved.")
                    st.rerun()

            with col2:
                if st.button("Reject", key=f"reject_{req_id}"):
                    db.collection("registration_requests").document(req_id).delete()
                    st.warning("Registration Rejected.")
                    st.rerun()

            st.divider()

    # ================= USER MANAGEMENT =================
    st.subheader("All Registered Users")

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
            role = user_data.get("role", "Member")
            is_blocked = user_data.get("is_blocked", False)

            status = "Blocked" if is_blocked else "Active"

            st.markdown(f"### {name} / {father_name}")
            st.write(f"Mobile: {mobile}")
            st.write(f"Role: {role}")
            st.write(f"Status: {status}")

            if st.button(
                "Unblock" if is_blocked else "Block",
                key=f"block_{user_id}"
            ):

                db.collection("users").document(user_id).update({
                    "is_blocked": not is_blocked,
                    "updated_at": datetime.utcnow()
                })

                st.success("User status updated.")
                st.rerun()

            st.divider()

    # ================= MEETING MANAGEMENT =================
    st.subheader("Meeting Management")

    meeting_ref = db.collection("admin_settings").document("meeting_options")
    meeting_doc = meeting_ref.get()
    meeting_data = meeting_doc.to_dict() if meeting_doc.exists else {}

    current_meeting_id = meeting_data.get("meeting_id")
    current_status = meeting_data.get("status", "Closed")

    col1, col2 = st.columns(2)
    col1.info(f"Meeting ID: {current_meeting_id if current_meeting_id else 'Not Set'}")
    col2.info(f"Status: {current_status}")

    st.divider()

    # Create / Activate Meeting
    with st.form("meeting_form"):

        new_meeting_id = st.text_input("Meeting ID")
        agenda_input = st.text_area("Agenda Options (comma separated)")
        date_input = st.text_area("Date Options (comma separated)")
        time_input = st.text_area("Time Options (comma separated)")
        place_input = st.text_area("Place Options (comma separated)")

        submit_meeting = st.form_submit_button("Save & Activate Meeting")

        if submit_meeting:

            if not new_meeting_id.strip():
                st.error("Meeting ID is required.")
            else:
                meeting_ref.set({
                    "meeting_id": new_meeting_id.strip(),
                    "agenda_options": [x.strip() for x in agenda_input.split(",") if x.strip()],
                    "date_options": [x.strip() for x in date_input.split(",") if x.strip()],
                    "time_options": [x.strip() for x in time_input.split(",") if x.strip()],
                    "place_options": [x.strip() for x in place_input.split(",") if x.strip()],
                    "status": "Active",
                    "created_at": datetime.utcnow()
                })

                st.success("Meeting activated.")
                st.rerun()

    # Close Meeting
    if current_status == "Active":

        st.divider()

        if st.checkbox("Confirm close meeting") and st.button("Close Meeting"):

            meeting_ref.update({"status": "Closed"})
            st.success("Meeting closed successfully.")
            st.rerun()
    if st.button("TEST WRITE"):
    db.collection("test_collection").add({
        "test": "working",
        "time": datetime.utcnow()
    })
    st.success("Write Successful")
