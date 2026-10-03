import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="TeamTrace AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom styles
css = Path("styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Sidebar
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

elif page == "My Meetings":
    st.title("My Meetings")
    st.caption("Your meeting history will appear here.")

elif page == "Upload Recording":
    st.title("Upload a meeting")
    st.caption("Upload an audio or video recording to get started.")

elif page == "Tasks":
    st.title("Tasks")
    st.caption("Your extracted action items will appear here.")

elif page == "Settings":
    st.title("Settings")
    st.caption("Manage your local workspace.")