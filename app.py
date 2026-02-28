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
