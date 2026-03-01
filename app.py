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
# ---------------- PUBLIC NOTICE BOARD ----------------
# ---------------- PUBLIC NOTICE BOARD ----------------
if menu == "Public Notice Board":

    st.title("📢 Public Notice Board")

    # ---------------- POST NOTICE (ALL USERS) ----------------
    st.subheader("📝 Post New Notice")

    if st.session_state.get("logged_in"):
        auto_name = f"{st.session_state.get('name','')} / {st.session_state.get('father_name','')}"
    else:
        auto_name = st.text_input("Your Name")

    notice_text = st.text_area("Write Notice")

    if st.button("Post Notice"):
        if notice_text.strip() != "" and auto_name.strip() != "":
            db.collection("notices").add({
                "notice": notice_text.strip(),
                "name_father": auto_name,
                "posted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "is_pinned": False
            })
            st.success("Notice Posted.")
            st.rerun()

    st.divider()

    # ---------------- FETCH NOTICES ----------------
    notices = db.collection("notices").stream()
    notice_list = []

    for notice_doc in notices:
        data = notice_doc.to_dict()
        data["doc_id"] = notice_doc.id
        notice_list.append(data)

    # Sort: pinned first, newest first
    notice_list = sorted(
        notice_list,
        key=lambda x: (
            x.get("is_pinned", False),
            x.get("posted_at", "")
        ),
        reverse=True
    )

    if len(notice_list) == 0:
        st.info("No notices available.")
    else:
        for data in notice_list:

            notice_id = data.get("doc_id")
            notice_text = data.get("notice", "")
            name_father = data.get("name_father", "Unknown")
            posted_at = data.get("posted_at", "")
            is_pinned = data.get("is_pinned", False)

            # Show pinned label
            if is_pinned:
                st.markdown("## 📌 Pinned Notice")

            st.markdown(f"### 🗞 {notice_text}")
            st.caption(f"Posted by: {name_father} | {posted_at}")

            # ---------------- PIN (ALL USERS) ----------------
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"Toggle Pin {notice_id}"):
                    db.collection("notices").document(notice_id).update({
                        "is_pinned": not is_pinned
                    })
                    st.rerun()

            # ---------------- EDIT (ADMIN ONLY) ----------------
            if st.session_state.get("role") == "Admin":
                with col2:
                    new_text = st.text_input(f"Edit Notice {notice_id}", value=notice_text)
                    if st.button(f"Save Edit {notice_id}"):
                        db.collection("notices").document(notice_id).update({
                            "notice": new_text.strip()
                        })
                        st.success("Notice Updated.")
                        st.rerun()

                # ---------------- DELETE (ADMIN ONLY) ----------------
                with col3:
                    if st.button(f"Delete {notice_id}"):
                        db.collection("notices").document(notice_id).delete()
                        st.success("Notice Deleted.")
                        st.rerun()

            st.divider()

            # ---------------- COMMENTS ----------------
            st.subheader("💬 Comments")

            comments = db.collection("notices") \
                .document(notice_id) \
                .collection("comments") \
                .stream()

            for c in comments:
                comment_data = c.to_dict()
                st.write(f"**{comment_data.get('name_father','User')}**")
                st.write(comment_data.get("comment",""))
                st.caption(comment_data.get("commented_at",""))
                st.divider()

            # ---------------- ADD COMMENT (ALL USERS) ----------------
            if st.session_state.get("logged_in"):
                comment_name = f"{st.session_state.get('name','')} / {st.session_state.get('father_name','')}"
            else:
                comment_name = st.text_input(f"Your Name {notice_id}")

            comment_text = st.text_input(f"Add Comment {notice_id}")

            if st.button(f"Comment {notice_id}"):

                if comment_text.strip() != "" and comment_name.strip() != "":
                    db.collection("notices") \
                        .document(notice_id) \
                        .collection("comments") \
                        .add({
                            "name_father": comment_name,
                            "comment": comment_text.strip(),
                            "commented_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        })

                    st.success("Comment Added.")
                    st.rerun()

            st.markdown("---")
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
        reg_mobile = st.text_input("Mobile Number (10 digits)")

        reg_submit = st.form_submit_button("Submit Registration")

        if reg_submit:

            reg_name = reg_name.strip()
            reg_father = reg_father.strip()
            reg_mobile = reg_mobile.strip()

            # ✅ Required Check
            if reg_name == "" or reg_father == "" or reg_mobile == "":
                st.warning("All fields are required.")
                st.stop()

            # ✅ Mobile Validation (10 digits only)
            if not reg_mobile.isdigit() or len(reg_mobile) != 10:
                st.error("Mobile number must be exactly 10 digits.")
                st.stop()

            # ✅ Check if already user
            existing_user = db.collection("users") \
                .where("mobile", "==", reg_mobile) \
                .stream()

            if list(existing_user):
                st.warning("User already registered. Please login.")
                st.stop()

            # ✅ Check if request already pending
            existing_request = db.collection("registration_requests") \
                .where("mobile", "==", reg_mobile) \
                .stream()

            if list(existing_request):
                st.warning("Registration already pending approval.")
                st.stop()

            # ✅ Save Registration Request
            db.collection("registration_requests").add({
                "name": reg_name,
                "father_name": reg_father,
                "mobile": reg_mobile,
                "status": "pending",
                "requested_at": datetime.utcnow()
            })

            st.success("Registration request submitted. Wait for admin approval.")
            st.rerun()
        # ================= MEETING MANAGEMENT =================
elif menu == "Meetings":

    import pandas as pd
    from datetime import datetime, timedelta

    st.title("📅 Meetings")

    # ================= GET CURRENT MEETING =================
    meeting_doc = db.collection("admin_settings").document("meeting_options").get()

    if not meeting_doc.exists:
        st.error("No meeting configured.")
        st.stop()

    meeting_data = meeting_doc.to_dict()
    meeting_id = meeting_data.get("meeting_id")
    meeting_status = meeting_data.get("status", "Closed")

    st.subheader("🟢 Current Meeting")
    st.info(f"Meeting ID: {meeting_id}")
    st.info(f"Status: {meeting_status}")

    # =========================================================
    # ================= ACTIVE MEETING ========================
    # =========================================================

    if meeting_status == "Active":

        st.divider()
        st.subheader("📝 Submit Attendance")

        # -------- USER INFO --------
        if st.session_state.get("logged_in"):
            auto_name = f"{st.session_state.name} / {st.session_state.father_name}"
            user_id = st.session_state.get("user_id")

            st.text_input("Your Name", value=auto_name, disabled=True)
            clean_name = auto_name.strip().lower()

        else:
            user_id = "public"
            name_input = st.text_input("Your Name")
            clean_name = name_input.strip().lower()

        # -------- FORM --------
        with st.form("attendance_form"):

            attending = st.radio("Will You Attend?", ["Yes", "No"])
            reason = st.text_area("Reason (Required if No)")
            submit = st.form_submit_button("Submit Attendance")

        if submit:

            if clean_name == "":
                st.warning("Name is required.")
                st.stop()

            if attending == "No" and reason.strip() == "":
                st.warning("Reason is required if not attending.")
                st.stop()

            # -------- DUPLICATE CHECK --------
            existing = db.collection("attendance_details") \
                .where("meeting_id", "==", meeting_id) \
                .where("user_id", "==", user_id) \
                .stream()

            if list(existing):
                st.error("Attendance already submitted.")
                st.stop()

            # -------- SAVE --------
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

    else:
        st.warning("Meeting is closed. Attendance disabled.")

    # =========================================================
    # ================= ARCHIVE SECTION =======================
    # =========================================================

    st.divider()
    st.subheader("📂 Meeting Archive (Last 3 Months)")

    three_months_ago = datetime.utcnow() - timedelta(days=90)

    archive_docs = db.collection("meeting_results").stream()
    archive_list = []

    for doc in archive_docs:
        data = doc.to_dict()
        finalized_at = data.get("finalized_at")

        if finalized_at:
            if isinstance(finalized_at, datetime):
                if finalized_at >= three_months_ago:
                    archive_list.append(data)

    if not archive_list:
        st.info("No archived meetings in last 3 months.")
        st.stop()

    meeting_ids = [m.get("meeting_id") for m in archive_list]

    selected_id = st.selectbox("Select Meeting ID", meeting_ids)

    archive_doc = db.collection("meeting_results").document(selected_id).get()

    if not archive_doc.exists:
        st.warning("No data found.")
        st.stop()

    archive_data = archive_doc.to_dict()

    # ================= FINAL RESULTS =================
    st.divider()
    st.subheader("🏆 Final Results")

    st.write(f"Total Votes: {archive_data.get('total_votes', 0)}")
    st.write(f"Winning Agenda: {archive_data.get('winning_agenda')}")
    st.write(f"Winning Date: {archive_data.get('winning_date')}")
    st.write(f"Winning Time: {archive_data.get('winning_time')}")
    st.write(f"Winning Place: {archive_data.get('winning_place')}")

    # ================= ATTENDANCE ANALYTICS =================
    st.divider()
    st.subheader("📊 Attendance Analytics")

    attendance_docs = db.collection("attendance_details") \
        .where("meeting_id", "==", selected_id) \
        .stream()

    attendance_list = []
    total_present = 0
    total_absent = 0

    for doc in attendance_docs:
        att = doc.to_dict()
        attendance_list.append(att)

        if att.get("attending") == "Yes":
            total_present += 1
        else:
            total_absent += 1

    total = total_present + total_absent

    if total > 0:

        col1, col2 = st.columns(2)
        col1.metric("Present", total_present)
        col2.metric("Absent", total_absent)

        df = pd.DataFrame(attendance_list)
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download Attendance CSV",
            csv,
            file_name=f"{selected_id}_attendance.csv",
            mime="text/csv"
        )

    else:
        st.info("No attendance data found.")
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

    st.title("👑 Admin Panel")

    # =========================================================
    # ================= REGISTRATION REQUESTS =================
    # =========================================================

    st.subheader("📝 Registration Requests")

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

            st.markdown(f"### 👤 {name} / {father_name}")
            st.write(f"📱 Mobile: {mobile}")

            col1, col2 = st.columns(2)

            # ===== APPROVE =====
            with col1:
                if st.button("✅ Approve", key=f"approve_{req_id}"):

                    # Prevent duplicate user creation
                    existing_user = db.collection("users") \
                        .where("mobile", "==", mobile) \
                        .stream()

                    if list(existing_user):
                        st.warning("User already exists.")
                        db.collection("registration_requests").document(req_id).delete()
                        st.rerun()

                    username = mobile
                    plain_password = mobile[-4:]  # Last 4 digits
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

                    st.success(
                        f"✅ User Approved!\n\nUsername: {username}\nPassword: {plain_password}"
                    )

                    st.rerun()

            # ===== REJECT =====
            with col2:
                if st.button("❌ Reject", key=f"reject_{req_id}"):

                    db.collection("registration_requests").document(req_id).delete()

                    st.warning("Registration Rejected.")
                    st.rerun()

            st.divider()

    # =========================================================
    # ================= MEETING MANAGEMENT ====================
    # =========================================================

    # ================= FETCH MEETING =================
    meeting_ref = db.collection("admin_settings").document("meeting_options")
    meeting_doc = meeting_ref.get()
    meeting_data = meeting_doc.to_dict() if meeting_doc.exists else {}

    current_meeting_id = meeting_data.get("meeting_id")
    current_status = meeting_data.get("status", "Closed")

    # ================= CURRENT STATUS =================
    st.subheader("📌 Current Meeting Status")

    col1, col2 = st.columns(2)
    col1.info(f"Meeting ID: {current_meeting_id if current_meeting_id else 'Not Set'}")
    col2.info(f"Status: {current_status}")

    st.divider()

    # ================= CREATE / UPDATE =================
    st.subheader("🛠 Create / Update Meeting")

    with st.form("meeting_form"):

        new_meeting_id = st.text_input("Meeting ID")

        agenda_input = st.text_area("Agenda Options (comma separated)")
        date_input = st.text_area("Date Options (comma separated)")
        time_input = st.text_area("Time Options (comma separated)")
        place_input = st.text_area("Place Options (comma separated)")

        submit_meeting = st.form_submit_button("💾 Save & Activate Meeting")

        if submit_meeting:

            if not new_meeting_id.strip():
                st.error("⚠ Meeting ID is required.")
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

                st.success("✅ Meeting saved and activated.")
                st.rerun()

    # ================= CLOSE MEETING =================
    if current_status == "Active":

        st.divider()
        st.subheader("🔒 Finalize Meeting")

        confirm_close = st.checkbox("I confirm to close this meeting")

        if confirm_close and st.button("🚨 Close Current Meeting"):

            votes_query = db.collection("meeting_details") \
                            .where("meeting_id", "==", current_meeting_id)

            votes = list(votes_query.stream())

            if not votes:
                st.error("⚠ No votes to finalize.")
                st.stop()

            agenda_count = {}
            date_count = {}
            time_count = {}
            place_count = {}

            for vote in votes:
                data = vote.to_dict()

                agenda = data.get("agenda")
                date = data.get("date")
                time = data.get("time")
                place = data.get("place")

                if agenda:
                    agenda_count[agenda] = agenda_count.get(agenda, 0) + 1
                if date:
                    date_count[date] = date_count.get(date, 0) + 1
                if time:
                    time_count[time] = time_count.get(time, 0) + 1
                if place:
                    place_count[place] = place_count.get(place, 0) + 1

            total_votes = len(votes)

            winning_agenda = max(agenda_count, key=agenda_count.get)
            winning_date = max(date_count, key=date_count.get)
            winning_time = max(time_count, key=time_count.get)
            winning_place = max(place_count, key=place_count.get)

            db.collection("meeting_results").document(current_meeting_id).set({
                "meeting_id": current_meeting_id,
                "total_votes": total_votes,
                "winning_agenda": winning_agenda,
                "winning_date": winning_date,
                "winning_time": winning_time,
                "winning_place": winning_place,
                "finalized_at": datetime.utcnow()
            })

            meeting_ref.update({"status": "Closed"})

            st.success("🎉 Meeting finalized and closed successfully.")
            st.rerun()
