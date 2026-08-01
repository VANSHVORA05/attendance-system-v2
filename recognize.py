import face_recognition
import cv2
import os
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------- GOOGLE SHEETS SETUP ----------
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)
sheet = client.open("Attendance Sheet").sheet1

# ---------- LOAD KNOWN FACES ----------
known_faces_dir = "known_faces"
known_encodings = []
known_names = []

print("Loading known faces...")
for filename in os.listdir(known_faces_dir):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(known_faces_dir, filename)
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            name = os.path.splitext(filename)[0]
            known_names.append(name)
            print(f"Loaded: {name}")
        else:
            print(f"Warning: No face found in {filename}, skipping.")

print(f"Total known faces loaded: {len(known_names)}")

# ---------- TRACK WHO'S ALREADY MARKED TODAY ----------
already_marked = set()

# ---------- START CAMERA ----------
cam = cv2.VideoCapture(0)
print("Starting camera. Press 'q' to quit.")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
        name = "Unknown"

        if True in matches:
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]

                # Mark attendance only once per person per run
                if name not in already_marked:
                    now = datetime.now()
                    date_str = now.strftime("%Y-%m-%d")
                    time_str = now.strftime("%H:%M:%S")
                    sheet.append_row([name, date_str, time_str])
                    already_marked.add(name)
                    print(f"Attendance marked: {name} at {time_str}")

        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        label = f"{name} - Marked" if name in already_marked else name

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("Attendance System - Press 'q' to quit", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()