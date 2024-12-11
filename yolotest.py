import time
import cv2
from ultralytics import YOLO

# Load a YOLO model
model = YOLO("best.engine")  # Replace with your model path

# Emotion labels
emotion_labels = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]

# Path to Haar Cascade
haar_cascade_path = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

# Open webcam stream
cap = cv2.VideoCapture(0)  # Change to video file path if needed

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(haar_cascade_path)

# Initialize variables for FPS calculation
prev_time = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to grayscale for face detection
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(
        gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    # Initialize a copy of the frame for annotation
    annotated_frame = frame.copy()

    if len(faces) == 0:
        # Process the whole frame if no faces are detected
        results = model.predict(source=frame, show=False)
        annotated_frame = results[0].plot()
    else:
        # Process each detected face
        for (x, y, w, h) in faces:
            if w > 0 and h > 0:  # Valid face region
                face_region = frame[y:y+h, x:x+w]

                # Check if face_region is valid
                if face_region.size == 0:
                    print("Warning: Detected face region is empty. Skipping...")
                    continue

                # Perform YOLO detection on the face region
                results = model.predict(source=face_region, show=False)

                # Annotate the face region with YOLO results
                for result in results[0].boxes:
                    x1, y1, x2, y2 = map(int, result.xyxy[0])

                    # Adjust coordinates relative to the original frame
                    x1 += x
                    y1 += y
                    x2 += x
                    y2 += y

                    # Get class index and confidence score
                    class_idx = int(result.cls[0]) if result.cls is not None else -1
                    conf = float(result.conf[0]) if result.conf is not None else 0.0

                    # Get the corresponding emotion label
                    label = emotion_labels[class_idx] if 0 <= class_idx < len(emotion_labels) else "Unknown"

                    # Draw bounding box and label on the annotated frame
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        annotated_frame,
                        f"{label} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

    # Calculate FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time != 0 else 0
    prev_time = curr_time

    # Add FPS text to the frame
    cv2.putText(
        annotated_frame, f"FPS: {fps:.2f}", (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA
    )

    # Display the annotated frame
    cv2.imshow("YOLO Emotion Detection", annotated_frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

