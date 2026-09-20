# Gujarat Smart CCTV — AI Prototype (Phase 1–5 starter)

Ye Gujarat Police Innovation Challenge 2026 ke liye ek chhota, real-chalne wala
prototype hai: video se vehicle/person detect karta hai, number plate padhta hai,
watchlist se match karta hai, aur police-style dashboard mein dikhata hai.

## Setup (ek baar karna hai)

```bash
python -m venv venv
source venv/bin/activate        # Windows par: venv\Scripts\activate
pip install -r requirements.txt
```

Pehli baar `detect.py` chalane par `yolov8n.pt` model automatically download
hoga (~6 MB) — internet chahiye ek baar.

## Test video kahan se laayen

Apna koi bhi road/traffic/CCTV-jaisa video chalega:
- Apne phone se 1 minute ka traffic/road video record kar lo, ya
- Free stock footage sites (Pexels, Pixabay) se "traffic" / "road" search karke
  koi bhi royalty-free video download kar lo.

File ko isi folder mein `sample.mp4` naam se rakh do.

## Chalane ka tarika

1. Detection + ANPR chalao:
   ```bash
   python detect.py --video sample.mp4 --camera CAM-01
   ```
   Isse `detections_log.csv` aur `annotated_CAM-01.mp4` (boxes ke saath video) banega.

   Agar OCR slow lag rahe (ANPR heavy hai), pehle sirf detection test karo:
   ```bash
   python detect.py --video sample.mp4 --camera CAM-01 --no-ocr
   ```

2. Dashboard dekho:
   ```bash
   streamlit run dashboard.py
   ```
   Browser mein khud khul jayega — stats, alerts, table, aur map dikhega.

3. Watchlist test karne ke liye `watchlist.csv` mein koi plate number daal do,
   aur video mein wahi number dikhne wali gaadi hone par "YES" match dikhega.
   (Real footage mein plate exact match karna mushkil hoga — demo ke liye tum
   khud ek plate ka photo/print bana ke test kar sakte ho.)

## Multiple cameras simulate karna

Same script ko alag-alag video/camera ID ke saath chalao:
```bash
python detect.py --video video1.mp4 --camera CAM-01
python detect.py --video video2.mp4 --camera CAM-02
```
Dono ka data ek hi `detections_log.csv` mein jama hoga — dashboard sab
cameras ka combined view dikhayega. (Yehi "cross-camera tracking" ka
starting point hai — Phase 3 mein isi log se "same plate kaun-kaun se
camera pe dikha" wala timeline banayenge.)

## Roadmap — ab aage kya

- [x] Phase 1: Vehicle/person detection (YOLOv8)
- [x] Phase 2: ANPR (EasyOCR) + watchlist match
- [x] Phase 5 (starter): Dashboard + map
- [ ] Phase 3: Cross-camera tracking — same plate ka multi-camera timeline
      (`detections_log.csv` ko plate_text + camera_id se group by karke banayenge)
- [ ] Phase 4: Real-time alert (dashboard already alert dikhata hai; agla step
      email/SMS/webhook notify karna hai — optional, agar time ho)
- [ ] Architecture diagram + demo video + GitHub repo (submission ke liye)

## Submission ke liye kya banana hai (jab time aaye)

1. GitHub repo (yeh code push karo)
2. 2-3 min demo video (dashboard + detection dikhate hue, screen record)
3. Architecture diagram (1 slide — camera → AI → dashboard → alert)
4. Short write-up: "abhi 1-4 cameras pe chal raha hai, architecture 80,000+
   cameras tak scale ho sakta hai" — is baat ko emphasize karna
