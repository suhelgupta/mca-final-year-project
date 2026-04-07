import cv2
import pickle
import time
import os

def check_user(open_camera=False) -> bool:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, 'face_recognizer.yml')
    labels_path = os.path.join(script_dir, 'labels.pkl')
    print(model_path)
    print(labels_path)
    # Load the trained model
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(model_path)
    except Exception as e:
        print(f"Error: Could not load the trained model. {e}")
        return False

    # Load the label dictionary
    try:
        with open(labels_path, 'rb') as f:
            label_dict = pickle.load(f)
    except Exception as e:
        print(f"Error: Could not load labels. {e}")
        return False

    # Reverse the dictionary for name lookup
    name_dict = {v: k for k, v in label_dict.items()}

    # Load Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Could not load Haar cascade.")
        return False

    # Open the camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return False

    print("Checking user... Look at the camera. Press 'q' to quit.")

    start_time = time.time()
    timeout = 10  # seconds to check

    while time.time() - start_time < timeout:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (100, 100))

            # Predict
            label, confidence = recognizer.predict(face)

            print(f"Predicted label: {label}, confidence: {confidence}", flush=True)  # Debug print

            # Draw rectangle and label
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            if confidence < 90:  # Adjust threshold as needed
                name = name_dict.get(label, "Unknown")
                cv2.putText(frame, f"{name} ({confidence:.2f})", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                if label in name_dict:
                    cap.release()
                    cv2.destroyAllWindows()
                    return True
            else:
                cv2.putText(frame, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        if open_camera:
            cv2.imshow('Face Recognition', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False

if __name__ == "__main__":
    result = check_user()
    print(f"User recognized: {result}")