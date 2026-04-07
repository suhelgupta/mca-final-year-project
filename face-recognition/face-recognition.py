import cv2
import os
import numpy as np
import pickle

def train_face_recognizer():
    # Path to the images folder
    data_path = os.path.join(os.path.dirname(__file__), 'img')
    if not os.path.exists(data_path):
        print(f"Error: '{data_path}' folder not found. Please create the 'img' folder with subfolders for each person containing their images.")
        return

    # Load Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if face_cascade.empty():
        print("Error: Could not load Haar cascade for face detection. Check OpenCV installation.")
        return

    # Initialize lists for faces and labels
    faces = []
    labels = []
    label_dict = {}
    label_id = 0

    # Check if there are subfolders (persons) or direct images
    subfolders = [f for f in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, f))]
    if subfolders:
        print(f"Found {len(subfolders)} person folders: {subfolders}")
        # Iterate through each subfolder (each person)
        for person_name in subfolders:
            person_path = os.path.join(data_path, person_name)
            if person_name not in label_dict:
                label_dict[person_name] = label_id
                label_id += 1

            image_count = 0
            face_count = 0
            # Iterate through images in the person's folder
            for image_name in os.listdir(person_path):
                image_path = os.path.join(person_path, image_name)
                if not image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                image_count += 1

                # Read the image
                image = cv2.imread(image_path)
                if image is None:
                    print(f"Warning: Could not read image {image_path}")
                    continue

                # Convert to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # Detect faces
                detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                if len(detected_faces) > 0:
                    face_count += 1
                    for (x, y, w, h) in detected_faces:
                        # Extract the face region
                        face = gray[y:y+h, x:x+w]
                        # Resize to a standard size (e.g., 100x100)
                        face = cv2.resize(face, (100, 100))
                        faces.append(face)
                        labels.append(label_dict[person_name])
                        break  # Use only one face per image
                else:
                    print(f"No face detected in {image_path}")

            print(f"Person {person_name}: {image_count} images, {face_count} with faces")
    else:
        # No subfolders, treat all images as one person
        print("No subfolders found. Treating all images in 'img' as one person.")
        person_name = input("Enter the name for the person: ").strip()
        if not person_name:
            person_name = 'person'
        label_dict[person_name] = 0
        image_count = 0
        face_count = 0
        for image_name in os.listdir(data_path):
            image_path = os.path.join(data_path, image_name)
            if not image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            image_count += 1

            image = cv2.imread(image_path)
            if image is None:
                print(f"Warning: Could not read image {image_path}")
                continue

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(detected_faces) > 0:
                face_count += 1
                for (x, y, w, h) in detected_faces:
                    face = gray[y:y+h, x:x+w]
                    face = cv2.resize(face, (100, 100))
                    faces.append(face)
                    labels.append(0)
                    break
            else:
                print(f"No face detected in {image_path}")

        print(f"Total: {image_count} images, {face_count} with faces")

    if len(faces) == 0:
        print("No faces detected in the images. Please check the image quality and folder structure.")
        return

    # Train the LBPH face recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))

    # Save the trained model
    recognizer.save('face_recognizer.yml')

    # Save the label dictionary
    with open('labels.pkl', 'wb') as f:
        pickle.dump(label_dict, f)

    print(f"Training completed. {len(faces)} faces trained for {len(label_dict)} people.")
    print("Model saved as 'face_recognizer.yml' and labels as 'labels.pkl'.")

if __name__ == "__main__":
    train_face_recognizer()
