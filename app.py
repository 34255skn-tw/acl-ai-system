import streamlit as st
import cv2
import mediapipe as mp
import time
import tempfile
import pandas as pd
from pose.mediapipe_pose import create_pose
from pose.landmarks import get_pose_points
from pose.drawing import draw_leg
from biomechanics.angles import calculate_angle
from biomechanics.velocity import calculate_velocity
from biomechanics.acceleration import calculate_acceleration
from biomechanics.asymmetry import calculate_asymmetry
from biomechanics.valgus import calculate_knee_valgus
from risk.acl_risk import acl_risk_score
from data.logger import SessionLogger
# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="ACL Biomechanics Intelligence System",
    layout="wide"
)
# =====================================
# CSS
# =====================================
st.markdown("""
<style>
.stApp{
    background:#0f172a;
}
h1,h2,h3{
    color:white;
}
[data-testid="stMetric"]{
    background:#1e293b;
    border:1px solid #334155;
    border-radius:15px;
    padding:15px;
}
section[data-testid="stSidebar"]{
    background:#111827;
}
</style>
""", unsafe_allow_html=True)
# =====================================
# HEADER
# =====================================
st.title("ACL Biomechanics Intelligence System")
st.markdown(
"""
Real-Time ACL Risk Analysis using MediaPipe and Biomechanics
"""
)
# =====================================
# SIDEBAR
# =====================================
st.sidebar.header("Athlete Profile")
age = st.sidebar.number_input(
    "Age",
    10,
    100,
    18
)
gender = st.sidebar.selectbox(
    "Gender",
    ["Male","Female"]
)
weight = st.sidebar.number_input(
    "Weight (kg)",
    20.0,
    200.0,
    60.0
)
height = st.sidebar.number_input(
    "Height (cm)",
    100.0,
    250.0,
    170.0
)
# =====================================
# KNOWLEDGE PANEL
# =====================================
tips = [
    "Landing with stiff knees increases ACL loading.",
    "Female athletes have higher ACL injury rates.",
    "Hamstring strength can help protect ACL.",
    "Poor landing mechanics increase injury risk.",
    "Large left-right asymmetry may indicate risk."
]
st.info(tips[int(time.time()) % len(tips)])
# =====================================
# START
# =====================================
st.subheader("Input Source")
mode=st.radio("Select Input",["Camera","Video File"])
uploaded_video=None
if mode=="Video File":
    uploaded_video=st.file_uploader("Upload Video",type=["mp4","avi","mov","mkv"])
run=st.button("Start Analysis")
save_data=st.button("Save Session")
if "logger" not in st.session_state:
    st.session_state.logger = SessionLogger()
logger = st.session_state.logger
# =====================================
# METRICS
# =====================================
col1,col2,col3,col4 = st.columns(4)
left_metric = col1.empty()
right_metric = col2.empty()
risk_metric = col3.empty()
asymmetry_metric = col4.empty()
col5,col6,col7,col8 = st.columns(4)
velocity_metric = col5.empty()
acceleration_metric = col6.empty()
left_valgus_metric = col7.empty()
right_valgus_metric = col8.empty()
frame_placeholder = st.empty()
chart_placeholder = st.empty()
# =====================================
# CAMERA LOOP
# =====================================
if run:
    pose = create_pose()
    mp_pose = mp.solutions.pose
    if mode=="Camera":
        cap=cv2.VideoCapture(0)
    else:
        if uploaded_video is None:
            st.warning("Please upload a video.")
            st.stop()
        temp_file=tempfile.NamedTemporaryFile(delete=False,suffix=".mp4")
        temp_file.write(uploaded_video.read())
        temp_file.close()
        cap=cv2.VideoCapture(temp_file.name)

    prev_left_angle = None
    prev_velocity = 0
    prev_time = time.time()
    history = []
    while True:
        success, frame = cap.read()
        if not success:
            st.error("Cannot access camera") if mode=="Camera" else st.success("Video analysis completed.")
            break
        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )
        results = pose.process(rgb)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            points = get_pose_points(
                landmarks,
                mp_pose
            )
            left_hip = points["left_hip"]
            left_knee = points["left_knee"]
            left_ankle = points["left_ankle"]
            right_hip = points["right_hip"]
            right_knee = points["right_knee"]
            right_ankle = points["right_ankle"]
            # =====================
            # ANGLES
            # =====================
            left_angle = calculate_angle(
                left_hip,
                left_knee,
                left_ankle
            )
            right_angle = calculate_angle(
                right_hip,
                right_knee,
                right_ankle
            )
            # =====================
            # ASYMMETRY
            # =====================
            asymmetry = calculate_asymmetry(
                left_angle,
                right_angle
            )
            # =====================
            # VALGUS
            # =====================
            left_valgus = calculate_knee_valgus(
                left_hip,
                left_knee,
                left_ankle
            )
            right_valgus = calculate_knee_valgus(
                right_hip,
                right_knee,
                right_ankle
            )
            # =====================
            # VELOCITY
            # =====================
            velocity = 0
            acceleration = 0
            current_time = time.time()
            if prev_left_angle is not None:
                dt = current_time - prev_time
                velocity = calculate_velocity(
                    left_angle,
                    prev_left_angle,
                    dt
                )
                acceleration = calculate_acceleration(
                    velocity,
                    prev_velocity,
                    dt
                )
            prev_left_angle = left_angle
            prev_velocity = velocity
            prev_time = current_time
            # =====================
            # RISK
            # =====================
            risk = acl_risk_score(
                left_angle,
                right_angle,
                asymmetry,
                left_valgus,
                right_valgus,
                velocity,
                age,
                gender
            )
            logger.add_record(

    time.time(),

    left_angle,

    right_angle,

    asymmetry,

    velocity,

    risk

)
            # =====================
            # STATUS
            # =====================
            if risk < 30:
                status = "LOW"
            elif risk < 60:
                status = "MODERATE"
            else:
                status = "HIGH"
            # =====================
            # DRAW
            # =====================
            draw_leg(
                frame,
                left_hip,
                left_knee,
                left_ankle
            )
            draw_leg(
                frame,
                right_hip,
                right_knee,
                right_ankle
            )
            cv2.putText(
                frame,
                f"Risk: {risk}",
                (20,40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,0,255),
                2
            )
            cv2.putText(
                frame,
                status,
                (20,80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0,255,255),
                2
            )
            # =====================
            # METRICS
            # =====================
            left_metric.metric(
                "Left Knee",
                f"{left_angle:.1f}°"
            )
            right_metric.metric(
                "Right Knee",
                f"{right_angle:.1f}°"
            )
            risk_metric.metric(
                "ACL Risk",
                f"{risk}%"
            )
            asymmetry_metric.metric(
                "Asymmetry",
                f"{asymmetry:.1f}%"
            )
            velocity_metric.metric(
                "Velocity",
                f"{velocity:.1f}"
            )
            acceleration_metric.metric(
                "Acceleration",
                f"{acceleration:.1f}"
            )
            left_valgus_metric.metric(
                "L Valgus",
                f"{left_valgus:.1f}"
            )
            right_valgus_metric.metric(
                "R Valgus",
                f"{right_valgus:.1f}"
            )
            history.append({
                "Left Knee":left_angle,
                "Right Knee":right_angle,
                "Risk":risk
            })
            if len(history) > 100:
                history.pop(0)
            chart_placeholder.line_chart(
                pd.DataFrame(history)
            )
        frame_placeholder.image(
            cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            ),
            channels="RGB",
            use_container_width=True
        )
    cap.release()

if save_data:
    filename = logger.save_csv()
    if filename:
        st.success(f"Saved to {filename}")
    else:
        st.warning("No data to save.")

        
        