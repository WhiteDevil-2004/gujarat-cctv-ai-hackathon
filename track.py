"""
Phase 3: Cross-Camera Vehicle Tracking
----------------------------------------
detections_log.csv mein jitni bhi baar ek plate number ALAG cameras pe
dikha hai, uska time-order timeline banata hai — "ye gaadi CAM-01 pe
10:21 baje dikhi, phir CAM-04 pe 10:27 baje" jaisa.

Chalane ka tarika (detect.py ko 2+ cameras ke liye chalane ke baad):
    python track.py
"""

import pandas as pd

LOG_FILE = "detections_log.csv"
OUT_FILE = "movement_history.csv"


def looks_like_plate(text):
    """Plate jaisa lagta hai ya nahi — kam se kam 1 digit ho, aur length 4-11 ho.
    Isse bus destination boards / street signs (jinme digit nahi hota) filter ho jate hain."""
    text = str(text).strip()
    if not (4 <= len(text) <= 11):
        return False
    return any(ch.isdigit() for ch in text)


def build_timelines():
    df = pd.read_csv(LOG_FILE)

    # Sirf wo rows jinme plate actually padha gaya (empty nahi) AUR plate-jaisa dikhta ho
    df = df[df["plate_text"].notna() & (df["plate_text"].astype(str).str.strip() != "")]
    df = df[df["plate_text"].apply(looks_like_plate)]

    if df.empty:
        print(
            "[INFO] Abhi koi plate number OCR se padha nahi gaya. "
            "Cross-camera tracking ke liye kam se kam ek readable plate chahiye. "
            "Watchlist test ke tarah, tum apna ek plate ka clear photo/print video mein dikha ke test kar sakte ho."
        )
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    timelines = []
    for plate, group in df.groupby("plate_text"):
        cameras_seen = group[["timestamp", "camera_id"]].drop_duplicates()
        for seq, (_, row) in enumerate(cameras_seen.iterrows(), start=1):
            timelines.append(
                {
                    "plate_text": plate,
                    "sequence": seq,
                    "camera_id": row["camera_id"],
                    "timestamp": row["timestamp"],
                }
            )

    result = pd.DataFrame(timelines)
    result.to_csv(OUT_FILE, index=False)

    print(f"[DONE] {OUT_FILE} ban gaya. Total {result['plate_text'].nunique()} unique plates track hui.\n")

    # Har plate ka readable timeline print karo
    for plate, group in result.groupby("plate_text"):
        path = " → ".join(f"{row.camera_id} ({row.timestamp.strftime('%H:%M:%S')})" for _, row in group.iterrows())
        cross_camera = group["camera_id"].nunique() > 1
        tag = "🔴 CROSS-CAMERA MOVEMENT" if cross_camera else "single camera only"
        print(f"{plate}  [{tag}]")
        print(f"  {path}\n")


if __name__ == "__main__":
    build_timelines()
