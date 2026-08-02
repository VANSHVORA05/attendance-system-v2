import streamlit as st
import face_recognition
import cv2
import os
import json
import time
import threading
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
from streamlit_autorefresh import st_autorefresh
import av

st.set_page_config(page_title="Rollcall", page_icon="●", layout="wide")

# ---------------- THEME: BLACK / WHITE / BLUE ----------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --accent: #3B82F6;
        --bg: #000000;
        --surface: #111111;
        --surface-2: #1A1A1A;
        --border: #2A2A2A;
        --text: #FFFFFF;
        --text-dim: #8A8A8A;
    }

    .stApp { background: var(--bg); font-family: 'Inter', sans-serif; }
    * { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }

    section[data-testid="stSidebar"] { background: var(--bg); border-right: 1px solid var(--border); }
    section[data-testid="stSidebar"] > div { padding-top: 2.2rem; }

    .brand-mark { font-size: 20px; font-weight: 700; color: var(--text); letter-spacing: -0.5px; margin-bottom: 4px; }
    .brand-dot { color: var(--accent); }
    .brand-tag { font-size: 12.5px; color: var(--text-dim); line-height: 1.6; margin-bottom: 28px; }

    .side-stat { padding: 14px 0; border-top: 1px solid var(--border); }
    .side-stat-label { font-size: 10.5px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; margin-bottom: 6px; }
    .side-stat-value { font-size: 28px; font-weight: 700; color: var(--text); }
    .side-stat-value.accent { color: var(--accent); }

    .rec-dot {
        display: inline-block; width: 7px; height: 7px; border-radius: 50%;
        background: var(--accent); margin-right: 7px; animation: pulse 1.4s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(59,130,246,0.5); }
        70% { box-shadow: 0 0 0 7px rgba(59,130,246,0); }
        100% { box-shadow: 0 0 0 0 rgba(59,130,246,0); }
    }

    .page-title { font-size: 32px; font-weight: 700; color: var(--text); letter-spacing: -0.7px; margin-bottom: 6px; }
    .page-sub { color: var(--text-dim); font-size: 15px; margin-bottom: 8px; }

    div[data-testid="stRadio"] > div {
        background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
        padding: 4px; display: inline-flex; gap: 2px;
    }
    div[data-testid="stRadio"] label { color: var(--text-dim) !important; font-weight: 500; font-size: 14px; padding: 6px 16px; border-radius: 7px; }

    .feed-card { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 14px; margin-top: 8px; }
    .feed-label { font-size: 12px; color: var(--text-dim); font-weight: 500; margin-bottom: 10px; display: flex; align-items: center; }

    div[data-testid="stButton"] button {
        background: var(--accent); color: #FFFFFF; font-weight: 600; font-size: 14px;
        border: none; border-radius: 9px; padding: 12px 0;
    }
    div[data-testid="stButton"] button p { color: #FFFFFF !important; }

    .log-card { background: var(--surface); border: 1px solid var(--border); border-left: 2px solid var(--accent); border-radius: 9px; padding: 12px 14px; margin-bottom: 8px; }
    .log-name { color: var(--text); font-size: 13.5px; font-weight: 600; }
    .log-meta { color: var(--text-dim); font-size: 11px; font-family: 'JetBrains Mono', monospace; margin-top: 2px; }

    .roster-row { display: flex; align-items: center; justify-content: space-between; background: var(--surface); border: 1px solid var(--border); border-radius: 9px; padding: 12px 16px; margin-bottom: 8px; }
    .roster-name { color: var(--text); font-size: 14px; font-weight: 600; }
    .roster-roll { color: var(--accent); font-size: 12px; font-weight: 600; font-family: 'JetBrains Mono', monospace; background: rgba(59,130,246,0.12); padding: 3px 10px; border-radius: 6px; }

    div[data-testid="stTextInput"] input { background: var(--surface-2) !important; color: var(--text) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
    hr { border-color: var(--border) !important; }

    .success-overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.92); backdrop-filter: blur(6px); z-index: 9999;
        display: flex; align-items: center; justify-content: center;
        animation: overlayIn 0.3s ease;
    }
    @keyframes overlayIn { from { opacity: 0; } to { opacity: 1; } }

    .success-card {
        background: var(--surface); border: 1px solid #333333; border-radius: 24px;
        padding: 56px 72px; text-align: center;
        animation: cardIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        box-shadow: 0 30px 80px rgba(0,0,0,0.7);
    }
    @keyframes cardIn { from { opacity: 0; transform: scale(0.85) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }

    .check-circle {
        width: 84px; height: 84px; border-radius: 50%;
        background: rgba(59,130,246,0.12); border: 2px solid var(--accent);
        display: flex; align-items: center; justify-content: center; margin: 0 auto 28px auto;
        animation: checkPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) 0.15s both;
    }
    .check-circle.error { background: rgba(239,68,68,0.12); border-color: #EF4444; }
    @keyframes checkPop { from { transform: scale(0); } to { transform: scale(1); } }
    .check-mark { font-size: 40px; color: var(--accent); font-weight: 700; }
    .check-mark.error { color: #EF4444; }

    .success-title { font-size: 30px; font-weight: 700; color: var(--text); margin-bottom: 10px; letter-spacing: -0.5px; }
    .success-name { font-size: 20px; font-weight: 600; color: var(--accent); margin-bottom: 4px; }
    .success-meta { font-size: 13px; color: var(--text-dim); font-family: 'JetBrains Mono', monospace; }
    </style>
""", unsafe_allow_html=True)

KNOWN_FACES_DIR = "known_faces"
ROLL_FILE = "roll_numbers.json"
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)


def load_roll_numbers():
    if os.path.exists(ROLL_FILE):
        with open(ROLL_FILE, "r") as f:
            return json.load(f)
    return {}


def save_roll_numbers(data):
    with open(ROLL_FILE, "w") as f:
        json.dump(data, f, indent=2)


@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Attendance Sheet").sheet1

@st.cache_resource
def load_known_faces():
    known_encodings, known_names = [], []
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(KNOWN_FACES_DIR, filename)
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if len(encodings) > 0:
                known_encodings.append(encodings[0])
                known_names.append(os.path.splitext(filename)[0])
    return known_encodings, known_names


roll_numbers = load_roll_numbers()
if "marked_today" not in st.session_state:
    st.session_state["marked_today"] = set()
marked_today = st.session_state["marked_today"]

if "scan_active" not in st.session_state:
    st.session_state["scan_active"] = False
if "pending_result" not in st.session_state:
    st.session_state["pending_result"] = None

try:
    sheet = get_sheet()
except Exception:
    sheet = None

known_encodings, known_names = load_known_faces()

# ---------------- SHARED STATE BETWEEN VIDEO THREAD AND MAIN THREAD ----------------
class ScanState:
    lock = threading.Lock()
    result = None  # dict with the outcome once a face has been processed
    frame_count = 0


class FaceRecognitionProcessor(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        with ScanState.lock:
            already_done = ScanState.result is not None

        if already_done:
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        ScanState.frame_count += 1
        if ScanState.frame_count % 5 == 0:
            rgb_frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
            face_locations = face_recognition.face_locations(small_frame)
            if not face_locations:
                return av.VideoFrame.from_ndarray(img, format="bgr24")
            face_encodings = face_recognition.face_encodings(small_frame, face_locations)

            if face_encodings:
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.45)
                    name = "Unknown"
                    if True in matches:
                        distances = face_recognition.face_distance(known_encodings, face_encoding)
                        best_match = np.argmin(distances)
                        if matches[best_match]:
                            name = known_names[best_match]

                    with ScanState.lock:
                        if ScanState.result is None:
                            if name == "Unknown":
                                ScanState.result = {"type": "error", "title": "Not recognized", "message": "This person may not be enrolled yet."}
                            elif name in st.session_state.get("marked_today", set()):
                                ScanState.result = {"type": "error", "title": f"{name.title()} already marked", "message": "Already checked in this session."}
                            else:
                                now = datetime.now()
                                roll_no = roll_numbers.get(name, "N/A")
                                sheet.append_row([name, roll_no, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")])
                                ScanState.result = {
                                    "type": "success", "name": name.title(), "roll": roll_no,
                                    "time": now.strftime("%H:%M:%S"), "raw_name": name
                                }
                    break

            for (top, right, bottom, left) in face_locations:
                top, right, bottom, left = top * 2, right * 2, bottom * 2, left * 2
                cv2.rectangle(img, (left, top), (right, bottom), (246, 130, 59), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown('<div class="brand-mark">Rollcall<span class="brand-dot">.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-tag">Attendance that takes itself — point a camera at the room and it does the rest.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-stat"><div class="side-stat-label">Enrolled</div><div class="side-stat-value">{len(known_names)}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-stat"><div class="side-stat-label">Marked today</div><div class="side-stat-value accent">{len(marked_today)}</div></div>', unsafe_allow_html=True)

    if st.button("Reset session", use_container_width=True):
        st.session_state["marked_today"] = set()
        st.rerun()

# ---------------- HEADER ----------------
st.markdown('<div class="page-title">Good to see you</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Start the camera once. Everything after that happens on its own.</div>', unsafe_allow_html=True)
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

page = st.radio(
    "Navigation",
    ["Take attendance", "Enroll student"],
    horizontal=True,
    label_visibility="collapsed",
)

# ==========================================================
# PAGE 1 — TAKE ATTENDANCE (fully automatic)
# ==========================================================
if page == "Take attendance":
    main_col, log_col = st.columns([2.2, 1])

    with log_col:
        st.markdown('<div class="side-stat-label" style="margin-bottom:10px;">Recent check-ins</div>', unsafe_allow_html=True)
        log_container = st.container()

    with main_col:
        st.markdown('<div class="feed-card">', unsafe_allow_html=True)
        st.markdown('<div class="feed-label"><span class="rec-dot"></span>Live scan</div>', unsafe_allow_html=True)

        if not st.session_state["scan_active"]:
            if st.button("Start camera", use_container_width=True):
                with ScanState.lock:
                    ScanState.result = None
                    ScanState.frame_count = 0
                st.session_state["scan_active"] = True
                st.rerun()
        else:
            webrtc_streamer(
                key="rollcall-scan",
                video_processor_factory=FaceRecognitionProcessor,
                media_stream_constraints={"video": True, "audio": False},
            )
            st_autorefresh(interval=700, key="poll_scan")

            with ScanState.lock:
                result_ready = ScanState.result

            if result_ready is not None:
                if result_ready["type"] == "success":
                    marked_today.add(result_ready["raw_name"])
                    st.session_state["marked_today"] = marked_today
                    with log_container:
                        st.markdown(
                            f'<div class="log-card"><div class="log-name">{result_ready["name"]}</div>'
                            f'<div class="log-meta">Roll {result_ready["roll"]} · {result_ready["time"]}</div></div>',
                            unsafe_allow_html=True
                        )
                st.session_state["pending_result"] = result_ready
                st.session_state["scan_active"] = False
                with ScanState.lock:
                    ScanState.result = None
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state["pending_result"] is not None:
        result = st.session_state["pending_result"]
        if result["type"] == "success":
            st.markdown(f"""
                <div class="success-overlay">
                    <div class="success-card">
                        <div class="check-circle"><span class="check-mark">✓</span></div>
                        <div class="success-title">Attendance marked</div>
                        <div class="success-name">{result["name"]}</div>
                        <div class="success-meta">Roll {result["roll"]} · {result["time"]}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="success-overlay">
                    <div class="success-card">
                        <div class="check-circle error"><span class="check-mark error">!</span></div>
                        <div class="success-title">{result["title"]}</div>
                        <div class="success-meta">{result["message"]}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        time.sleep(2.2)
        st.session_state["pending_result"] = None
        st.rerun()

# ==========================================================
# PAGE 2 — ENROLL STUDENT
# ==========================================================
else:
    st.markdown('<div class="side-stat-label" style="margin-bottom:16px;">Register a new student</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        new_name = st.text_input("Full name")
    with col_b:
        new_roll = st.text_input("Roll number")

    if "show_enroll_camera" not in st.session_state:
        st.session_state["show_enroll_camera"] = False

    if not st.session_state["show_enroll_camera"]:
        if st.button("Open camera to capture photo", use_container_width=True):
            st.session_state["show_enroll_camera"] = True
            st.rerun()
    else:
        captured_photo = st.camera_input("Capture face photo", key="enroll_input")

        if st.button("Cancel", use_container_width=True):
            st.session_state["show_enroll_camera"] = False
            st.rerun()

        if captured_photo is not None:
            if not new_name.strip() or not new_roll.strip():
                st.error("Enter both name and roll number.")
            else:
                file_bytes = np.asarray(bytearray(captured_photo.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                rgb_check = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                face_check = face_recognition.face_encodings(rgb_check)

                if len(face_check) == 0:
                    st.error("No face detected. Try again with better lighting.")
                else:
                    save_path = os.path.join(KNOWN_FACES_DIR, f"{new_name.strip().lower()}.jpg")
                    cv2.imwrite(save_path, img)
                    roll_numbers[new_name.strip().lower()] = new_roll.strip()
                    save_roll_numbers(roll_numbers)
                    st.success(f"{new_name} (Roll {new_roll}) enrolled.")
                    st.session_state["show_enroll_camera"] = False
                    st.cache_resource.clear()
                    st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="side-stat-label">Roster</div>', unsafe_allow_html=True)
    if roll_numbers:
        for name, roll in roll_numbers.items():
            st.markdown(f'<div class="roster-row"><span class="roster-name">{name.title()}</span><span class="roster-roll">Roll {roll}</span></div>', unsafe_allow_html=True)
    else:
        st.caption("No students enrolled yet.")