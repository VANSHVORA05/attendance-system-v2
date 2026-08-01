import cv2

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Camera not found or not accessible!")
else:
    print("Camera opened successfully. Press 'q' to close.")

while True:
    ret, frame = cam.read()
    if not ret:
        break
    cv2.imshow("Test Camera", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()