# Walkthrough - DeepFace + MediaPipe + MySQL Voting System

I have successfully refactored the project to use **DeepFace** (no C++ build tools required), **MediaPipe** (robust liveness), and **MySQL**.

## 🚀 How to Run

1.  **MySQL Setup**:
    - Ensure your MySQL server is running (e.g., via XAMPP or MySQL Workbench).
    - Default config assumes: `User: root`, `Password: [empty]`, `Host: localhost`.
    - If you have a different password, update [config.py](file:///e:/z_projects/eye%20recogize/config.py).

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The first time you run the app, DeepFace will download the VGG-Face model weights (~500MB). This is normal.*

3.  **Run the App**:
    ```bash
    streamlit run app.py
    ```

## 🗳️ Features & Usage

### 1. Register Voter
- Navigate to the **Register** menu.
- Enter **Name**.
- Click **Take Photo**.
- Click **Register Voter**. *Wait for "User Registered Successfully!" message.*

### 2. Vote (with Liveness Check)
- Navigate to the **Vote** menu.
- Click **Start Verification**.
- **Blink your eyes** at the camera. The system uses MediaPipe Face Mesh to detect blinks.
- Once liveness is verified, it matches your face using DeepFace.
- If recognized, you can cast your vote.
- Duplicate voting is preventing by checking the MySQL database.

### 3. Admin Dashboard
- Navigate to the **Admin** menu.
- View real-time **Results**.
- View **Attendance Log** (Data fetched from MySQL).

## 🛠️ Tech Stack Changes

- **Face Recognition**: Switched from `dlib` to `DeepFace` (VGG-Face model). Eliminates complex C++ compilation errors.
- **Liveness Detection**: Switched from Haar Cascades to `MediaPipe Face Mesh`. More accurate and works better with different lighting.
- **Database**: Switched from SQLite to `MySQL`. Improved scalability and data management.
