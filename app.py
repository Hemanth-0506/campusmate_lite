import os
from datetime import date, time

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

st.set_page_config(
    page_title="CampusMate Lite",
    page_icon="🎓",
    layout="wide",
)

# ---------- Session state ----------
DEFAULTS = {
    "student_profile": {
        "name": "",
        "branch": "CSE",
        "regulation": "A22",
        "year": "3rd Year",
        "semester": "I Semester",
        "commute_minutes": 90,
        "sleep_hours": 8.0,
        "study_hours_weekday": 2.0,
        "study_hours_weekend": 4.0,
        "goals": "Prepare consistently for semester exams",
    },
    "curriculum_file_name": "",
    "almanac_file_name": "",
    "timetable_file_name": "",
    "ai_messages": [],
    "plan": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, dict) else value

profile = st.session_state.student_profile

# ---------- Helpers ----------
def get_client():
    if not ENDPOINT or not API_KEY or not DEPLOYMENT:
        raise RuntimeError(
            "Azure configuration is incomplete. Check AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT in your local .env file."
        )
    return OpenAI(api_key=API_KEY, base_url=f"{ENDPOINT}/openai/v1/")


def ask_campusmate(question, context):
    client = get_client()
    instructions = (
        "You are CampusMate Lite, an academic assistant for college students. "
        "Explain concepts clearly, use examples, and structure answers for students. "
        "Do not claim to have read a document unless its contents are provided. "
        "Do not invent official curriculum details, examination dates, or college rules. "
        "When relevant information is missing, say what is missing and ask for it. "
        "Distinguish verified facts from suggestions."
    )
    response = client.responses.create(
        model=DEPLOYMENT,
        instructions=instructions + "\n\nStudent context:\n" + context,
        input=question,
    )
    return response.output_text or "The model returned an empty response."


def build_student_context():
    p = st.session_state.student_profile
    return (
        f"Branch: {p['branch']}; Regulation: {p['regulation']}; "
        f"Year: {p['year']}; Semester: {p['semester']}; "
        f"Commute per day: {p['commute_minutes']} minutes; "
        f"Sleep target: {p['sleep_hours']} hours; "
        f"Preferred weekday study time: {p['study_hours_weekday']} hours; "
        f"Preferred weekend study time: {p['study_hours_weekend']} hours; "
        f"Academic goals: {p['goals']}. "
        "No verified timetable or parsed curriculum content is currently supplied to the AI."
    )


def estimate_weekly_capacity(weekday_hours, weekend_hours):
    return max(0.0, weekday_hours) * 5 + max(0.0, weekend_hours) * 2


# ---------- Sidebar / navigation ----------
with st.sidebar:
    st.title("🎓 CampusMate Lite")
    st.caption("Your curriculum. Your schedule. Your semester.")
    page = st.radio(
        "Navigate",
        ["Dashboard", "My Curriculum", "Study Planner", "AI Study Assistant"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Development build")
    st.caption("Uploaded documents are not yet automatically parsed.")

# ---------- Header ----------
st.title(page)
if page == "Dashboard":
    st.caption("A personalized academic planning workspace.")
elif page == "My Curriculum":
    st.caption("Keep your academic reference documents together.")
elif page == "Study Planner":
    st.caption("Plan study time around your real availability.")
else:
    st.caption("Ask academic questions with your student context.")

# ---------- Dashboard ----------
if page == "Dashboard":
    p = st.session_state.student_profile
    capacity = estimate_weekly_capacity(
        float(p["study_hours_weekday"]), float(p["study_hours_weekend"])
    )

    st.subheader("Your semester at a glance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Academic profile", f"{p['branch']} · {p['regulation']}")
    c2.metric("Current semester", f"{p['year']} · {p['semester']}")
    c3.metric("Preferred study capacity", f"{capacity:g} hrs/week")

    st.subheader("Setup status")
    docs = [
        ("Curriculum", st.session_state.curriculum_file_name),
        ("Academic almanac", st.session_state.almanac_file_name),
        ("Class timetable", st.session_state.timetable_file_name),
    ]
    for label, filename in docs:
        if filename:
            st.write(f"✓ **{label}:** {filename}")
        else:
            st.write(f"○ **{label}:** Not added yet")

    st.info(
        "Start with **My Curriculum** to add your curriculum, semester almanac, "
        "and section-specific timetable. Then complete your profile in **Study Planner**. "
        "This build stores uploaded filenames for the current session; document extraction "
        "and timetable verification are the next development milestone."
    )

    st.subheader("Next steps")
    st.markdown(
        "- Add and verify your academic documents.\n"
        "- Enter your actual weekly availability and upcoming deadlines.\n"
        "- Generate a study plan based on verified subjects and available time."
    )

# ---------- My Curriculum ----------
elif page == "My Curriculum":
    st.write(
        "Add the documents CampusMate will use as academic references. "
        "Your curriculum and almanac may be shared college documents; your timetable "
        "should match your own section."
    )

    with st.form("document_setup_form"):
        curriculum = st.file_uploader(
            "Curriculum / syllabus PDF",
            type=["pdf", "docx", "txt"],
            key="curriculum_upload",
            help="Use the official curriculum for your branch and regulation.",
        )
        almanac = st.file_uploader(
            "Academic calendar / semester almanac",
            type=["pdf", "docx", "xlsx", "csv", "txt"],
            key="almanac_upload",
        )
        timetable = st.file_uploader(
            "Your class / section timetable",
            type=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"],
            key="timetable_upload",
            help="Upload the timetable for your actual section.",
        )
        submitted = st.form_submit_button("Save document selections", type="primary")

    if submitted:
        st.session_state.curriculum_file_name = curriculum.name if curriculum else ""
        st.session_state.almanac_file_name = almanac.name if almanac else ""
        st.session_state.timetable_file_name = timetable.name if timetable else ""
        st.success("Document selections saved for this session.")

    st.divider()
    st.subheader("Document verification")
    st.warning(
        "For now, this page records the selected filenames only. It does not yet extract "
        "or verify document contents. Do not treat a file as processed until the next "
        "development milestone adds extraction and a review screen."
    )
    st.markdown(
        "**Before using a generated plan, we will verify:**\n"
        "- Branch, regulation, year, and semester match.\n"
        "- Subject names and syllabus units match the official curriculum.\n"
        "- Almanac dates and examination periods are read correctly.\n"
        "- Timetable days, lecture slots, and labs match your section."
    )

# ---------- Study Planner ----------
elif page == "Study Planner":
    st.write(
        "Set your normal routine and academic goals. The current build calculates "
        "your stated weekly study capacity; timetable-aware scheduling will be added next."
    )

    with st.form("student_profile_form"):
        st.subheader("Academic profile")
        name = st.text_input("Name (optional)", value=profile["name"])
        col1, col2 = st.columns(2)
        with col1:
            branch = st.selectbox(
                "Branch",
                ["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil", "Other"],
                index=["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil", "Other"].index(
                    profile["branch"]
                ) if profile["branch"] in ["CSE", "IT", "ECE", "EEE", "Mechanical", "Civil", "Other"] else 0,
            )
            regulation = st.text_input("Regulation", value=profile["regulation"])
            year = st.selectbox(
                "Year",
                ["1st Year", "2nd Year", "3rd Year", "4th Year"],
                index=["1st Year", "2nd Year", "3rd Year", "4th Year"].index(profile["year"]),
            )
            semester = st.selectbox(
                "Semester",
                ["I Semester", "II Semester"],
                index=["I Semester", "II Semester"].index(profile["semester"]),
            )
        with col2:
            commute = st.number_input(
                "Total daily commute (minutes)",
                min_value=0,
                max_value=600,
                value=int(profile["commute_minutes"]),
                step=15,
            )
            sleep = st.number_input(
                "Target sleep per night (hours)",
                min_value=0.0,
                max_value=16.0,
                value=float(profile["sleep_hours"]),
                step=0.5,
            )
            weekday = st.number_input(
                "Available study hours per weekday",
                min_value=0.0,
                max_value=16.0,
                value=float(profile["study_hours_weekday"]),
                step=0.5,
            )
            weekend = st.number_input(
                "Available study hours per weekend day",
                min_value=0.0,
                max_value=16.0,
                value=float(profile["study_hours_weekend"]),
                step=0.5,
            )
        goals = st.text_area(
            "Academic goals",
            value=profile["goals"],
            placeholder="e.g. prepare for internal exams, revise DSA, complete assignments",
        )
        save_profile = st.form_submit_button("Save my profile", type="primary")

    if save_profile:
        st.session_state.student_profile = {
            "name": name.strip(),
            "branch": branch,
            "regulation": regulation.strip(),
            "year": year,
            "semester": semester,
            "commute_minutes": int(commute),
            "sleep_hours": float(sleep),
            "study_hours_weekday": float(weekday),
            "study_hours_weekend": float(weekend),
            "goals": goals.strip(),
        }
        profile = st.session_state.student_profile
        st.success("Student profile saved for this session.")

    p = st.session_state.student_profile
    weekly_capacity = estimate_weekly_capacity(
        float(p["study_hours_weekday"]), float(p["study_hours_weekend"])
    )
    st.divider()
    st.subheader("Current availability estimate")
    st.metric("Preferred weekly study capacity", f"{weekly_capacity:g} hours")
    st.caption(
        "This is based on the hours you entered, not yet cross-checked against your uploaded "
        "class timetable. It is a capacity estimate, not a generated study schedule."
    )

    st.subheader("What the full planner will generate")
    st.markdown(
        "- Semester roadmap: week, subject, verified topics, planned hours, target.\n"
        "- Weekly timetable: day, time, activity, duration.\n"
        "- Daily tasks: priority, task, estimated duration, completion status.\n"
        "- Warnings when requested study time exceeds your available capacity or conflicts "
        "with classes and other commitments."
    )

# ---------- AI Study Assistant ----------
elif page == "AI Study Assistant":
    st.write(
        "Ask a concept question or request help organizing your studies. Until document "
        "extraction is implemented, uploaded files are not included as source material."
    )

    with st.expander("Student context currently sent to the assistant"):
        st.text(build_student_context())

    question = st.text_area(
        "What would you like help with?",
        placeholder="Example: Explain operating system deadlocks with a simple example.",
        height=120,
        key="academic_question",
    )

    if st.button("Generate Answer", type="primary"):
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            try:
                with st.spinner("CampusMate is thinking..."):
                    answer = ask_campusmate(question.strip(), build_student_context())
                st.session_state.ai_messages.append(
                    {"question": question.strip(), "answer": answer}
                )
            except Exception as exc:
                st.error("CampusMate could not complete the request.")
                st.caption(
                    "Check that your local Azure configuration is present and the deployment "
                    "is available. Detailed diagnostics are shown below for development."
                )
                with st.expander("Technical details"):
                    st.write("Error type:", type(exc).__name__)
                    st.code(str(exc))

    if st.session_state.ai_messages:
        st.subheader("Recent answers")
        for index, item in enumerate(reversed(st.session_state.ai_messages[-5:]), start=1):
            with st.container(border=True):
                st.markdown(f"**Question:** {item['question']}")
                st.markdown(item["answer"])

st.divider()
st.caption(
    "CampusMate Lite · Development build · Verify official academic dates and syllabus "
    "details against college documents."
)
