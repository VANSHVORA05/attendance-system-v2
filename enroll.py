import cv2
import os

name = input("Enter student name: ").strip()
folder = "known_faces"
os.makedirs(folder, exist_ok=True)

cam = cv2.VideoCapture(0)
print("Look at the camera. Press 's' to save the photo, 'q' to quit without saving.")

while True:
    ret, frame = cam.read()
    if not ret:
        break
    cv2.imshow("Enroll Student - Press 's' to save", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        filepath = os.path.join(folder, f"{name}.jpg")
        cv2.imwrite(filepath, frame)
        print(f"Saved: {filepath}")
        break
    elif key == ord('q'):
        print("Cancelled.")
        break

cam.release()
cv2.destroyAllWindows()