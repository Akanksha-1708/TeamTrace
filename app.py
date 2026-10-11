
import streamlit as st
from pathlib import Path
import uuid
import json

from core import (
    initialize_db,
    get_meetings,
    get_meeting,
    transcribe_recording,
    format_timestamp,
    analyze_meeting,
    save_meeting,
)

# -----------------------------
# Initialize application
# -----------------------------

st.set_page_config(
    page_title="TeamTrace AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_db()

if "navigation_target" in st.session_state:
    st.session_state["page_nav"] = st.session_state.pop(
        "navigation_target"
    )

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# -----------------------------
# Load custom styles
# -----------------------------

css_path = Path("styles.css")

if css_path.exists():
    css = css_path.read_text(encoding="utf-8")
    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )

# -----------------------------
# Sidebar navigation
# -----------------------------

with st.sidebar:
    st.markdown("## ✦ TeamTrace AI")
    st.caption("Meeting intelligence")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "My Meetings",
            "Upload Recording",
            "Tasks",
            "Settings",
        ],
        key="page_nav",
        label_visibility="visible",
    )

    st.divider()

    st.markdown(
        """
        <div class="sidebar-footer">
            <div class="avatar">A</div>
            <div>
                <b>Akanksha</b><br>
                <small>Local workspace</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Dashboard
# -----------------------------

if page == "Dashboard":
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="eyebrow">WORKSPACE / OVERVIEW</div>
                <h1>Good evening, Akanksha 👋</h1>
                <p>Here's what's happening across your meetings.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    meetings = get_meetings()
    total_meetings = len(meetings)

    total_tasks = 0
    total_decisions = 0
    total_questions = 0

    for meeting in meetings:
        try:
            analysis = json.loads(meeting["analysis"])
            total_tasks += len(analysis.get("tasks", []))
            total_decisions += len(analysis.get("decisions", []))
            total_questions += len(analysis.get("questions", []))
        except (json.JSONDecodeError, TypeError):
            continue

    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        (col1, "Total meetings", total_meetings, "◷"),
        (col2, "Tasks extracted", total_tasks, "☑"),
        (col3, "Decisions made", total_decisions, "✦"),
        (col4, "Open questions", total_questions, "?"),
    ]

    for col, label, value, icon in metrics:
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-icon">{icon}</div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])

    with left:
        st.markdown("### Recent meetings")
        st.caption("Your latest saved meetings")

        with st.container(border=True):
            if not meetings:
                st.info("No saved meetings yet.")
            else:
                for meeting in meetings[:5]:
                    st.markdown(f"**{meeting['title']}**")
                    st.caption(
                        f"{meeting['recording_name'] or 'Recording'}"
                        f" · {meeting['created_at']}"
                    )
                    st.divider()

    with right:
        st.markdown("### Get started")

        with st.container(border=True):
            st.markdown("#### Turn a conversation into action")
            st.write(
                "Upload a recording to extract topics, "
                "tasks, decisions, and open questions."
            )

            if st.button(
                "＋ Upload a meeting",
                use_container_width=True,
            ):
                st.session_state["navigation_target"] = (
                    "Upload Recording"
                )
                st.rerun()

# -----------------------------
# Upload Recording
# -----------------------------

elif page == "Upload Recording":
    st.markdown(
        """
        <div class="page-header">
            <div class="eyebrow">WORKSPACE / NEW MEETING</div>
            <h1>Upload a recording</h1>
            <p>Turn your team's conversations into organized insights.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("### Meeting recording")
        st.caption("Select an audio or video file from your device.")

        uploaded_file = st.file_uploader(
            "Choose a recording",
            type=[
                "mp3", "wav", "m4a", "mp4",
                "mov", "mkv", "webm",
            ],
            accept_multiple_files=False,
            help="Supported formats: MP3, WAV, M4A, MP4, MOV, MKV, WEBM",
        )

        if uploaded_file:
            size_mb = uploaded_file.size / (1024 * 1024)

            st.markdown(
                f"""
                <div class="upload-file-card">
                    <div class="meeting-icon">♫</div>
                    <div class="meeting-info">
                        <b>{uploaded_file.name}</b>
                        <small>{size_mb:.2f} MB · Ready to upload</small>
                    </div>
                    <span class="status-pill">Selected</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if size_mb > 500:
                st.error("File exceeds the 500 MB application limit.")
            elif st.button(
                "Upload recording",
                type="primary",
                use_container_width=True,
            ):
                suffix = Path(uploaded_file.name).suffix.lower()
                safe_name = f"{uuid.uuid4().hex}{suffix}"
                destination = UPLOAD_DIR / safe_name

                try:
                    with destination.open("wb") as file:
                        file.write(uploaded_file.getbuffer())

                    st.session_state["last_uploaded_file"] = str(
                        destination
                    )
                    st.session_state["last_recording_name"] = (
                        uploaded_file.name
                    )

                    # Clear results from the previous recording.
                    for key in (
                        "transcription_result",
                        "meeting_analysis",
                        "saved_meeting_id",
                    ):
                        st.session_state.pop(key, None)

                    st.success("Recording uploaded successfully.")
                    st.caption(f"Saved as: {safe_name}")

                except OSError as error:
                    st.error(f"Could not save the recording: {error}")
        else:
            st.info("Your recording will appear here once selected.")

    # Transcription
    saved_path = st.session_state.get("last_uploaded_file")

    if saved_path and Path(saved_path).exists():
        st.markdown("### Transcription")

        if st.button(
            "Generate transcript",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "Loading Faster-Whisper and transcribing..."
                ):
                    result = transcribe_recording(saved_path)

                st.session_state["transcription_result"] = result
                st.session_state.pop("meeting_analysis", None)
                st.session_state.pop("saved_meeting_id", None)

                st.success("Transcription completed.")

            except Exception as error:
                st.error(f"Transcription failed: {error}")

    result = st.session_state.get("transcription_result")

    # Display transcript
    if result:
        st.markdown("### Transcript")

        st.caption(
            f"Language: {result['language']} · "
            f"Duration: {result['duration']:.1f} seconds"
        )

        with st.container(border=True):
            for segment in result["segments"]:
                timestamp = format_timestamp(segment["start"])
                st.markdown(f"**{timestamp}**")
                st.write(segment["text"])
                st.divider()

        # -----------------------------
        # Mistral AI meeting analysis
        # -----------------------------

        st.markdown("### Meeting Intelligence")

        if st.button(
            "Generate AI Insights",
            type="primary",
            use_container_width=True,
        ):
            transcript_text = "\n".join(
                segment["text"]
                for segment in result["segments"]
            )

            try:
                with st.spinner("Mistral is analyzing your meeting..."):
                    analysis = analyze_meeting(transcript_text)

                st.session_state["meeting_analysis"] = analysis
                st.session_state.pop("saved_meeting_id", None)

                st.success("AI analysis completed!")

            except Exception as error:
                st.error(f"AI analysis failed: {error}")

        analysis = st.session_state.get("meeting_analysis")

        if analysis:
            st.markdown("#### Summary")
            st.write(analysis.get("summary", "No summary available."))

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Key Topics")

                for topic in analysis.get("topics", []):
                    st.markdown(f"- {topic}")

                st.markdown("#### Decisions")

                for decision in analysis.get("decisions", []):
                    st.markdown(f"- {decision}")

            with col2:
                st.markdown("#### Action Items")

                for task in analysis.get("tasks", []):
                    if isinstance(task, dict):
                        st.markdown(
                            f"**{task.get('task', 'Task')}**"
                        )
                        st.caption(
                            f"Assignee: {task.get('assignee') or 'Unassigned'}"
                            f" · Deadline: {task.get('deadline') or 'Not specified'}"
                        )
                    else:
                        st.markdown(f"- {task}")

                st.markdown("#### Open Questions")

                for question in analysis.get("questions", []):
                    st.markdown(f"- {question}")

            # -----------------------------
            # Save meeting
            # -----------------------------

            st.divider()
            st.markdown("### Save this meeting")

            default_title = Path(
                st.session_state.get(
                    "last_recording_name",
                    Path(saved_path).name,
                )
            ).stem

            meeting_title = st.text_input(
                "Meeting title",
                value=default_title,
                key="meeting_title_input",
            )

            if st.session_state.get("saved_meeting_id"):
                st.success(
                    "This meeting has already been saved "
                    f"(ID: {st.session_state['saved_meeting_id']})."
                )
            elif st.button(
                "Save Meeting",
                use_container_width=True,
            ):
                try:
                    transcript_text = "\n".join(
                        segment["text"]
                        for segment in result["segments"]
                    )

                    meeting_id = save_meeting(
                        title=meeting_title.strip() or default_title,
                        recording_name=Path(saved_path).name,
                        transcript=transcript_text,
                        analysis=analysis,
                    )

                    st.session_state["saved_meeting_id"] = meeting_id
                    st.success(
                        f"Meeting saved successfully! ID: {meeting_id}"
                    )

                except Exception as error:
                    st.error(f"Could not save meeting: {error}")

    st.caption(
        "Recordings and meeting history are stored locally. "
        "Transcription runs locally using Faster-Whisper; "
        "AI analysis uses the Mistral API."
    )

# -----------------------------
# My Meetings
# -----------------------------

elif page == "My Meetings":
    st.title("My Meetings")
    st.caption("Your saved meeting history")

    meetings = get_meetings()

    if not meetings:
        st.info("No meetings saved yet. Process and save a recording first.")
    else:
        meeting_options = {
            f"{meeting['title']} · {meeting['created_at']} "
            f"(ID: {meeting['id']})": meeting["id"]
            for meeting in meetings
        }

        selected_label = st.selectbox(
            "Select a meeting",
            list(meeting_options.keys()),
        )

        if selected_label:
            meeting_id = meeting_options[selected_label]
            meeting = get_meeting(meeting_id)

            if meeting:
                st.markdown(f"### {meeting['title']}")
                st.caption(
                    f"Recording: {meeting['recording_name'] or 'Unknown'}"
                    f" · Created: {meeting['created_at']}"
                )

                st.markdown("#### Transcript")
                st.write(meeting["transcript"])

                st.markdown("#### Meeting Intelligence")

                try:
                    analysis = json.loads(meeting["analysis"])

                    st.markdown("##### Summary")
                    st.write(analysis.get("summary", ""))

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("##### Key Topics")
                        for topic in analysis.get("topics", []):
                            st.markdown(f"- {topic}")

                        st.markdown("##### Decisions")
                        for decision in analysis.get("decisions", []):
                            st.markdown(f"- {decision}")

                    with col2:
                        st.markdown("##### Action Items")
                        for task in analysis.get("tasks", []):
                            if isinstance(task, dict):
                                st.markdown(
                                    f"**{task.get('task', 'Task')}**"
                                )
                                st.caption(
                                    f"Assignee: {task.get('assignee') or 'Unassigned'}"
                                    f" · Deadline: {task.get('deadline') or 'Not specified'}"
                                )
                            else:
                                st.markdown(f"- {task}")

                        st.markdown("##### Open Questions")
                        for question in analysis.get("questions", []):
                            st.markdown(f"- {question}")

                except (json.JSONDecodeError, TypeError):
                    st.error("Could not read this meeting's saved analysis.")

# -----------------------------
# Tasks
# -----------------------------

elif page == "Tasks":
    st.title("Tasks")
    st.caption("Action items extracted from your saved meetings")

    meetings = get_meetings()
    all_tasks = []

    for meeting in meetings:
        try:
            analysis = json.loads(meeting["analysis"])

            for task in analysis.get("tasks", []):
                if isinstance(task, dict):
                    all_tasks.append({
                        "meeting": meeting["title"],
                        "task": task.get("task", "Task"),
                        "assignee": task.get("assignee"),
                        "deadline": task.get("deadline"),
                    })
                else:
                    all_tasks.append({
                        "meeting": meeting["title"],
                        "task": str(task),
                        "assignee": None,
                        "deadline": None,
                    })

        except (json.JSONDecodeError, TypeError):
            continue

    if not all_tasks:
        st.info("No tasks found. Analyze and save a meeting first.")
    else:
        for task in all_tasks:
            with st.container(border=True):
                st.markdown(f"**{task['task']}**")
                st.caption(f"Meeting: {task['meeting']}")
                st.write(
                    f"Assignee: {task['assignee'] or 'Unassigned'}"
                )
                st.write(
                    f"Deadline: {task['deadline'] or 'Not specified'}"
                )

# -----------------------------
# Settings
# -----------------------------

elif page == "Settings":
    st.title("Settings")
    st.caption("Manage your local workspace.")

    st.markdown("### AI provider")
    st.write("Mistral AI API")
    st.caption(
        "AI analysis requires internet access and a valid "
        "MISTRAL_API_KEY in your .env file."
    )

    st.markdown("### Storage")
    st.write(f"Meeting database: `{Path('teamtrace.db').resolve()}`")
    st.write(f"Recording directory: `{UPLOAD_DIR.resolve()}`")
