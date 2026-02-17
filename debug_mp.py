try:
    import mediapipe as mp
    print("MediaPipe imported successfully")
    print(f"Version: {mp.__version__}")
    print(f"Solutions: {mp.solutions}")
except Exception as e:
    import traceback
    traceback.print_exc()
