
import streamlit as st
from pathlib import Path
import uuid

st.set_page_config(
    page_title="TeamTrace AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)
if "navigation_target" in st.session_state:
    st.session_state["page_nav"]=st.session_state.pop("navigation_target")

# Paths
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Load custom styles
css = Path("styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Sidebar navigation
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
            "Settings"
        ],
        key="page_nav",
        label_visibility="visible"
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
        unsafe_allow_html=True
    )

# Dashboard
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
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        (col1, "Total meetings", "12", "◷"),
        (col2, "Tasks extracted", "28", "☑"),
        (col3, "Decisions made", "15", "✦"),
        (col4, "Open questions", "06", "?")
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
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.5, 1])

    with left:
        st.markdown("### Recent meetings")
        st.caption("Your latest processed recordings")

        with st.container(border=True):
            for name, date, duration, status in [
                ("Project Planning Discussion", "Oct 03, 2026", "42 min", "Processed"),
                ("Hackathon Team Call", "Oct 02, 2026", "35 min", "Processed"),
                ("Frontend Design Review", "Oct 01, 2026", "28 min", "Processed"),
            ]:
                st.markdown(
                    f"""
                    <div class="meeting-row">
                        <div class="meeting-icon">◈</div>
                        <div class="meeting-info">
                            <b>{name}</b>
                            <small>{date} · {duration}</small>
                        </div>
                        <span class="status-pill">{status}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with right:
        st.markdown("### Get started")
        with st.container(border=True):
            st.markdown("#### Turn a conversation into action")
            st.write(
                "Upload an audio or video recording to extract "
                "topics, tasks, decisions, and timelines."
            )

            if st.button("＋ Upload a meeting", use_container_width=True):
                st.session_state["navigation_target"] = "Upload Recording"
                st.rerun()

# Upload page
elif page == "Upload Recording":
    st.markdown(
        """
        <div class="page-header">
            <div class="eyebrow">WORKSPACE / NEW MEETING</div>
            <h1>Upload a recording</h1>
            <p>Turn your team's conversations into organized, actionable insights.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.markdown("### Meeting recording")
        st.caption("Select an audio or video file from your device.")

        uploaded_file = st.file_uploader(
            "Choose a recording",
            type=["mp3", "wav", "m4a", "mp4", "mov", "mkv", "webm"],
            accept_multiple_files=False,
            help="Supported formats: MP3, WAV, M4A, MP4, MOV, MKV, WEBM"
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
                unsafe_allow_html=True
            )

            if size_mb > 500:
                st.error("File exceeds the 500 MB application limit.")
            else:
                if st.button(
                    "Upload recording",
                    type="primary",
                    use_container_width=True
                ):
                    suffix = Path(uploaded_file.name).suffix.lower()
                    safe_name = f"{uuid.uuid4().hex}{suffix}"
                    destination = UPLOAD_DIR / safe_name

                    try:
                        with destination.open("wb") as file:
                            file.write(uploaded_file.getbuffer())

                        st.session_state["last_uploaded_file"] = str(destination)
                        st.session_state.pop("transcription_result", None)
                        st.success("Recording uploaded successfully.")
                        st.caption(f"Saved as: {safe_name}")

                    except OSError as error:
                        st.error(f"Could not save the recording: {error}")

        else:
            st.info("Your recording will appear here once selected.")

    # Transcription action for the saved recording
    saved_path=st.session_state.get("last_uploaded_file")
    if saved_path and Path(saved_path).exists():
        st.markdown("### Transcription")
        if st.button("Generate transcript", type="primary",use_container_width=True):
            from core import transcribe_recording
            try:
                with st.spinner("Loading Whisper and transcribing your recording..."):
                    result=transcribe_recording(saved_path)
                
                st.session_state["transcription_result"]=result
                st.success("Transcription completed.")

            except Exception as error:
                st.error(f"Transcription failed: {error}")

    result=st.session_state.get("transcription_result")

    if result:
        st.markdown("### Transcript")
        st.caption(
            f"Language: {result['language']} · "
            f"Duration: {result['duration']:.1f} seconds"
        )
        from core import format_timestamp
        with st.container(border=True):
            for segment in result["segments"]:
                timestamp=format_timestamp(segment["start"])
                st.markdown(f"**{timestamp}**")
                st.write(segment["text"])
                st.divider()

    st.caption(
        "Recordings are stored locally. Transcrition runs locally"
        "using Faster-Whisper."
    )  

# Other pages
elif page == "My Meetings":
    st.title("My Meetings")
    st.caption("Your meeting history will appear here.")

elif page == "Tasks":
    st.title("Tasks")
    st.caption("Your extracted action items will appear here.")

elif page == "Settings":
    st.title("Settings")
    st.caption("Manage your local workspace.")
