from deepface import DeepFace
import numpy as np
import pickle
from scipy.spatial.distance import cosine

# Note: We no longer load/save from local pickle file.
# Embeddings are stored in MySQL.

def register(img):
    """
    Generates embedding for the face.
    Returns: embedding list/array if successful, else None.
    """
    try:
        # DeepFace expects BGR or RGB.
        embedding_objs = DeepFace.represent(img_path = img, model_name = "VGG-Face", enforce_detection = True)
        
        if embedding_objs:
            embedding = embedding_objs[0]["embedding"]
            return embedding
        return None
    except Exception as e:
        print(f"Error registering face: {e}")
        return None

def recognize(img, known_faces_dict):
    """
    Recognizes face/identity from the image using the provided known_faces_dict.
    known_faces_dict format: { 'username': embedding_array, ... }
    """
    try:
        if not known_faces_dict: return None

        # Get embedding for the input image
        embedding_objs = DeepFace.represent(img_path = img, model_name = "VGG-Face", enforce_detection = True)
        
        if not embedding_objs:
            return None
        
        target_embedding = embedding_objs[0]["embedding"]
        
        min_dist = 100
        identity = None
        
        # VGG-Face + Cosine usually has a threshold around 0.40
        threshold = 0.40

        for name, db_embedding in known_faces_dict.items():
            dist = cosine(target_embedding, db_embedding)
            if dist < min_dist:
                min_dist = dist
                identity = name
        
        if min_dist < threshold:
            return identity
        
        return None
    except Exception as e:
        # print(f"Error recognizing face: {e}")
        return None

def check_face_exists(img, known_faces_dict):
    """
    Checks if the face in 'img' already exists in the provided known_faces_dict.
    Returns the username if it exists, otherwise None.
    """
    # Reuse recognize logic as it does exactly this: finds best match in known list
    return recognize(img, known_faces_dict)
