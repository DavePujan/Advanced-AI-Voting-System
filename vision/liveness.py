import cv2
import time

# Load Haar Cascades
# cv2.data.haarcascades gives the path to xml files
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Blink State Machine
STATE_EYES_OPEN = 0
STATE_EYES_CLOSED = 1
current_state = STATE_EYES_OPEN
blink_counter = 0

last_blink_time = 0

def check_liveness(frame):
    global current_state, blink_counter, last_blink_time
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    eyes_detected = False
    
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        
        # Detect eyes within the face
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 4)
        
        if len(eyes) >= 1:
            eyes_detected = True
            break # Found eyes in at least one face

    # Blink Logic
    # Transition: OPEN -> CLOSED -> OPEN = BLINK
    
    timestamp = time.time()
    
    if current_state == STATE_EYES_OPEN:
        if not eyes_detected:
            # Maybe blinking?
            current_state = STATE_EYES_CLOSED
            
    elif current_state == STATE_EYES_CLOSED:
        if eyes_detected:
            # Eyes re-opened! Blink confirmed.
            current_state = STATE_EYES_OPEN
            blink_counter += 1
            last_blink_time = timestamp
            return True # Return true on the frame the blink finishes
        
    # Reset if closed for too long (might be lost tracking)
    # But for now, simple is fine.
    
    return False

def reset_liveness():
    global blink_counter
    blink_counter = 0
