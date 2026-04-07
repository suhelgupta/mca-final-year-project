import sys
import os

# Add the face-recognition folder to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'face-recognition'))

from check_user import check_user

if __name__ == "__main__":
    print("Checking user authentication...")
    if check_user(True):
        print("User recognized. Access granted.")
        # Add your main application code here
        print("Welcome to the application!")
    else:
        print("User not recognized. Access denied.")
        # Optionally, exit or handle denial
        exit(1)
