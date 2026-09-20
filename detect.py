"""
Phase 1 + Phase 2: CCTV AI Detection + ANPR
--------------------------------------------
Kaam kya karta hai:
1. Ek video file ko "CCTV camera feed" jaisa treat karta hai
2. YOLOv8 (pretrained) se vehicle/person detect karta hai
3. Har vehicle ke liye number plate crop karke EasyOCR se padhta hai
4. Watchlist (watchlist.csv) se match check karta hai
5. Sab kuch detections_log.csv mein save karta hai + annotated video banata hai

Kaise chalayen:
    python detect.py --video sample.mp4 --camera CAM-01

Agar --video nahi diya to laptop webcam use hoga (camera index 0).
"""

import argparse
import csv
import os
import re
import time
from datetime import datetime

import cv2
from ultralytics import YOLO

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck"}
PERSON_CLASS = "person"
LOG_FILE = "detections_log.csv"
WATCHLIST_FILE = "watchlist.csv"


def load_watchlist(path=WATCHLIST_FILE):
    plates = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[0].strip():
                    plates.add(row[0].strip().upper().replace(" ", ""))
    return plates


def clean_plate_text(text):
    # OCR se aaya text saaf karo — sirf letters/numbers rakho
    text = re.sub(r"[^A-Za-z0-9]", "", text).upper()
    return text


def looks_like_plate(text):
    """Plate jaisa lagta hai ya nahi — kam se kam 1 digit ho, aur length 4-11 ho.
    Isse bus destination boards / street signs (jinme digit nahi hota) filter ho jate hain."""
    if not (4 <= len(text) <= 11):
        return False
    return any(ch.isdigit() for ch in text)


def init_log():
    is_new = not os.path.exists(LOG_FILE)
    f = open(LOG_FILE, "a", newline="", encoding="utf-8")
    writer = csv.writer(f)
    if is_new:
        writer.writerow(
            ["timestamp", "camera_id", "object_class", "confidence", "plate_text", "watchlist_match"]
        )
    return f, writer


def run(video_source, camera_id, show_window, use_ocr, resize_width, skip):
    model = YOLO("yolov8n.pt")  # pretrained, chhota aur fast model
    reader = None
    if use_ocr:
        import easyocr

        reader = easyocr.Reader(["en"], gpu=False)

    watchlist = load_watchlist()
    log_file, writer = init_log()

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"[ERROR] Video/camera nahi khul raha: {video_source}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 20
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # CPU par speed ke liye frame ko chhota kar dete hain (aspect ratio maintain)
    if resize_width and resize_width < orig_width:
        scale = resize_width / orig_width
        width, height = resize_width, int(orig_height * scale)
    else:
        width, height = orig_width, orig_height

    out = cv2.VideoWriter(
        f"annotated_{camera_id}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )

    frame_count = 0
    start_time = time.time()
    print(f"[INFO] {camera_id} shuru ho gaya. Processing size: {width}x{height}. Ctrl+C se rok sakte ho.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_count += 1

        if (width, height) != (orig_width, orig_height):
            frame = cv2.resize(frame, (width, height))

        # Speed ke liye har Nth frame pe hi detection chalao (--skip se control hota hai)
        if frame_count % skip == 0:
            results = model(frame, verbose=False)[0]
            for box in results.boxes:
                cls_name = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                if conf < 0.4:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                plate_text = ""
                watchlist_match = "NO"

                if cls_name in VEHICLE_CLASSES and reader is not None:
                    crop = frame[max(0, y1):y2, max(0, x1):x2]
                    if crop.size > 0:
                        ocr_results = reader.readtext(crop)
                        if ocr_results:
                            candidate = clean_plate_text(
                                max(ocr_results, key=lambda r: r[2])[1]
                            )
                            if looks_like_plate(candidate):
                                plate_text = candidate
                                if plate_text in watchlist:
                                    watchlist_match = "YES"

                if cls_name in VEHICLE_CLASSES or cls_name == PERSON_CLASS:
                    writer.writerow(
                        [
                            datetime.now().isoformat(timespec="seconds"),
                            camera_id,
                            cls_name,
                            round(conf, 2),
                            plate_text,
                            watchlist_match,
                        ]
                    )

                color = (0, 0, 255) if watchlist_match == "YES" else (0, 200, 0)
                label = f"{cls_name} {conf:.2f}" + (f" | {plate_text}" if plate_text else "")
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, max(0, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        out.write(frame)

        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            print(f"[PROGRESS] Frame {frame_count} processed | {elapsed:.1f}s elapsed")

        if show_window:
            cv2.imshow(camera_id, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    out.release()
    log_file.close()
    cv2.destroyAllWindows()
    total_time = time.time() - start_time
    print(f"[DONE] {frame_count} frames in {total_time:.1f}s. Log: {LOG_FILE} | Video: annotated_{camera_id}.mp4")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=str, default="0", help="video file path, ya webcam ke liye 0")
    parser.add_argument("--camera", type=str, default="CAM-01", help="camera ID (simulate karne ke liye)")
    parser.add_argument("--show-window", action="store_true", help="live preview window dikhao (CPU par isse aur glitch/slow ho sakta hai)")
    parser.add_argument("--no-ocr", action="store_true", help="ANPR/OCR skip karo (sirf detection, fast)")
    parser.add_argument("--resize", type=int, default=960, help="processing ke liye frame width chhota karo (default 960, speed ke liye). 0 = original size")
    parser.add_argument("--skip", type=int, default=5, help="har Nth frame pe detection chalao (default 5, higher = fast)")
    args = parser.parse_args()

    src = 0 if args.video == "0" else args.video
    run(
        src,
        args.camera,
        show_window=args.show_window,
        use_ocr=not args.no_ocr,
        resize_width=args.resize if args.resize > 0 else None,
        skip=max(1, args.skip),
    )
