import sys
import os

# Add folders with hyphens to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'face-recognition'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hand-guesture'))

from ui import launch

if __name__ == "__main__":
    launch()

