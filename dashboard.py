"""
Phase 5: Police Command Dashboard
----------------------------------
detect.py chalane ke baad ye dashboard uska detections_log.csv padh ke
live-style police dashboard dikhata hai: alerts, stats, table, aur map.

Chalane ka tarika:
    streamlit run dashboard.py
"""

import os

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

LOG_FILE = "detections_log.csv"

# Demo ke liye fake camera locations (Ahmedabad ke aas-paas).
# Real deployment mein ye Gujarat Police ke actual camera coordinates honge.
CAMERA_LOCATIONS = {
    "CAM-01": (23.0225, 72.5714),
    "CAM-02": (23.0300, 72.5800),
    "CAM-03": (23.0100, 72.5600),
    "CAM-04": (23.0400, 72.5900),
}

st.set_page_config(page_title="Gujarat Smart CCTV Command", layout="wide")
st.title("🚨 Gujarat Smart CCTV Command Dashboard (Prototype)")

if not os.path.exists(LOG_FILE):
    st.warning(
        "Abhi tak koi detection log nahi mila. Pehle `python detect.py --video sample.mp4` chalao, "
        "phir is dashboard ko refresh karo."
    )
    st.stop()

df = pd.read_csv(LOG_FILE)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cameras Active", df["camera_id"].nunique())
col2.metric("Total Detections", len(df))
col3.metric("Vehicles Detected", (df["object_class"] != "person").sum())
col4.metric("Watchlist Alerts", (df["watchlist_match"] == "YES").sum())

st.divider()

alert_df = df[df["watchlist_match"] == "YES"]
if len(alert_df) > 0:
    st.error(f"🔴 {len(alert_df)} WATCHLIST MATCH ALERT(S) FOUND!")
    st.dataframe(alert_df, use_container_width=True)
else:
    st.success("🟢 Koi watchlist match nahi mila abhi tak.")

st.subheader("📋 Full Detection Log")
st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

st.divider()
st.subheader("🔗 Cross-Camera Vehicle Tracking (Phase 3)")

MOVEMENT_FILE = "movement_history.csv"
selected_plate = None
if os.path.exists(MOVEMENT_FILE):
    movement_df = pd.read_csv(MOVEMENT_FILE)
    plates = sorted(movement_df["plate_text"].unique())
    if plates:
        selected_plate = st.selectbox("Plate number choose karo timeline dekhne ke liye", plates)
        plate_path = movement_df[movement_df["plate_text"] == selected_plate].sort_values("sequence")
        st.dataframe(plate_path, use_container_width=True)
        n_cams = plate_path["camera_id"].nunique()
        if n_cams > 1:
            st.error(f"🔴 Ye vehicle {n_cams} alag cameras pe dikhi — cross-camera movement confirmed!")
        else:
            st.info("Ye vehicle abhi sirf ek camera pe dikhi hai.")
    else:
        st.info("Movement file khali hai — abhi koi plate track nahi hui.")
else:
    st.info(
        "`track.py` abhi nahi chalaya gaya. Do ya zyada cameras ke liye detect.py chalane ke baad "
        "`python track.py` chalao, phir yahan timeline dikhega."
    )

st.subheader("🗺️ Camera Network Map")
m = folium.Map(location=[23.0225, 72.5714], zoom_start=13)
for cam_id, (lat, lon) in CAMERA_LOCATIONS.items():
    cam_alerts = alert_df[alert_df["camera_id"] == cam_id]
    color = "red" if len(cam_alerts) > 0 else "green"
    folium.Marker(
        [lat, lon],
        popup=f"{cam_id} — {len(df[df['camera_id'] == cam_id])} detections",
        icon=folium.Icon(color=color),
    ).add_to(m)

# Agar plate select hui hai aur uska route bana hai, to map par line kheencho
if selected_plate is not None and os.path.exists(MOVEMENT_FILE):
    plate_path = movement_df[movement_df["plate_text"] == selected_plate].sort_values("sequence")
    route_points = [
        CAMERA_LOCATIONS[cam] for cam in plate_path["camera_id"] if cam in CAMERA_LOCATIONS
    ]
    if len(route_points) > 1:
        folium.PolyLine(route_points, color="blue", weight=4, opacity=0.8).add_to(m)

st_folium(m, width=1200, height=450)

st.caption(
    "Prototype note: camera locations abhi demo/fake hain. Real deployment mein Gujarat Police "
    "ke actual camera GPS coordinates use honge."
)
