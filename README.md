# ASD Screening & Video Analysis Platform

This project is a Flask-based autism screening and behavioral analysis platform. It combines a tabular section-based assessment pipeline with an optional video-based behavior analysis module.

## Current Working Flow

The application is structured around three main assessment sections plus an optional video analysis module:

1. **Section 1 - Assessment**: medical and developmental history
2. **Section 2 - Screening**: autism screening questionnaire
3. **Section 3 - Observation**: behavioral observation based on CARS and SRS scales
4. **Video Analysis**: optional behavioral insights from pose landmark detection
5. **Final Analysis**: aggregates the latest results from all sections

## Main Files and Responsibilities

### `main.py`
The primary Flask application.
- Handles user signup, login, dashboard, history, and final_analysis.
- Loads the three section-specific machine learning models:
  - `section1_model.pkl`
  - `section2_model.pkl`
  - `section3_model.pkl`
- Implements the current section flow:
  - `/assessment` → Section 1 form and prediction
  - `/screening` and `/submit` → Section 2 questionnaire and prediction
  - `/assessment2` → Section 3 observation and prediction
  - `/final_analysis` → aggregated report page
- Saves results to MySQL via `db.py` and stores them in `screening_history`.
- Registers the `videoanalysis` blueprint under `/videoanalysis`.

### `db.py`
A simple MySQL connection helper.
- Defines `get_db_connection()`.
- Current connection settings are:
  - host: `localhost`
  - user: `root`
  - password: `12345`
  - database: `autism_db`

### `app.py`
A separate standalone predictor demo.
- Loads `dreamdataset_model.pkl`.
- Provides a lightweight `/predict` endpoint.
- Accepts form inputs such as age, gender, communication, interaction, play, stereotype, and SCQ score.
- This file is independent of the main three-section workflow.

## Video Analysis Package

### `videoanalysis/__init__.py`
- Marks the package as a Python module.
- Allows `main.py` to import `videoanalysis` components.

### `videoanalysis/pose_detector.py`
- Loads the MediaPipe Pose Landmarker model from `pose_landmarker_full.task`.
- Converts frames from OpenCV BGR to MediaPipe RGB.
- Detects pose landmarks and returns the first person detected.

### `videoanalysis/scoring.py`
- Computes behavioral scores from pose landmarks.
- Produces:
  - `eye_contact` / face direction
  - `attention`
  - `movement`
  - `asd_score`
  - `risk`
- Tracks wrist movement across sampled frames to calculate repetitive movement.

### `videoanalysis/video_processor.py`
- Reads uploaded videos using OpenCV.
- Samples one frame every 5 frames for performance.
- Detects pose landmarks and calculates scores per frame.
- Aggregates average results and summary text for the report.

### `videoanalysis/report_generator.py`
- Generates a Matplotlib graph from video analysis scores:
  - `eye_scores`
  - `attention_scores`
  - `movement_scores`
- Saves the graph to `videoanalysis/static/graph.png`.

### `videoanalysis/pdf_report.py`
- Builds a styled PDF report with ReportLab.
- Includes overall risk, summary text, metrics, and the graph image.
- Saves the report to `videoanalysis/static/report.pdf`.

## Templates Modified

The following templates were updated to reflect the current three-section flow and cleaner wording:
- `templates/assessment.html`
- `templates/screening.html`
- `templates/assessment2.html`
- `templates/final_analysis.html`
- `templates/dashboard.html`
- `templates/home.html`

## Session Flow and Connections Between Files

### Session 1 - Assessment (Developmental History)
- **User Flow**: `/assessment` route → form submission → `/submit` route
- **Template**: `templates/assessment.html` → collects medical and developmental history
- **Model**: `section1_model.pkl` loaded in `main.py`
- **Database**: Results saved to MySQL `screening_history` table via `db.py`
- **Features Used**: Age, speech delay, learning disorder, genetic disorders, family history of ASD, jaundice, depression, anxiety
- **Output**: Risk classification (Low/Moderate/High) stored in session

### Session 2 - Screening (Behavioral Questionnaire)
- **User Flow**: `/screening` route → questionnaire form → `/submit` route
- **Template**: `templates/screening.html` → collects A1-A10 autism screening responses
- **Model**: `section2_model.pkl` loaded in `main.py`
- **Database**: Results saved to MySQL `screening_history` table via `db.py`
- **Features Used**: A1 through A10 autism spectrum quotient questions
- **Output**: Autism trait likelihood score stored in session

### Session 3 - Observation (Clinical Observation)
- **User Flow**: `/assessment2` route → observation form → `/submit` route
- **Template**: `templates/assessment2.html` → collects CARS and SRS scores
- **Model**: `section3_model.pkl` loaded in `main.py`
- **Database**: Results saved to MySQL `screening_history` table via `db.py`
- **Features Used**: Childhood Autism Rating Scale, Social Responsiveness Scale, age, sex, anxiety, depression
- **Output**: Behavioral observation risk score stored in session

### Session 4 - Video Analysis (Optional Behavioral Insights)
- **User Flow**: `/videoanalysis/` → video upload → `/videoanalysis/analyze` route
- **Pipeline**: 
  1. `videoanalysis/video_processor.py` reads the video using OpenCV
  2. `videoanalysis/pose_detector.py` detects pose landmarks using MediaPipe
  3. `videoanalysis/scoring.py` calculates behavioral metrics (eye contact, attention, movement)
  4. `videoanalysis/report_generator.py` creates visualization graph
  5. `videoanalysis/pdf_report.py` generates final PDF report
- **Storage**: Graph saved to `videoanalysis/static/graph.png`, PDF to `videoanalysis/static/report.pdf`
- **Output**: Video-based risk classification (Low/Moderate/High) with visual and PDF reports

### Final Analysis - Integration of All Sessions
- **Route**: `/final_analysis` in `main.py`
- **Template**: `templates/final_analysis.html`
- **Logic**: Aggregates the latest results from:
  - Session 1 (Assessment) risk
  - Session 2 (Screening) autism trait score
  - Session 3 (Observation) behavioral risk
  - Session 4 (Video Analysis) - if available and completed
- **Computation**: Combines scores using weighted average or ensemble logic
- **Database**: Retrieves all saved section results from MySQL via `db.py`
- **Output**: Comprehensive ASD screening report for review by healthcare professionals

### File Interdependencies

```
main.py (orchestrator)
├── db.py (database operations)
│   └── MySQL: screening_history table
├── section1_model.pkl → Assessment form
├── section2_model.pkl → Screening form
├── section3_model.pkl → Observation form
└── videoanalysis/ (blueprint registration)
    ├── __init__.py
    ├── pose_detector.py (MediaPipe integration)
    ├── scoring.py (metric calculations)
    ├── video_processor.py (video reading & sampling)
    ├── report_generator.py (Matplotlib graphs)
    ├── pdf_report.py (ReportLab PDF generation)
    ├── pose_landmarker_full.task (MediaPipe model asset)
    └── static/ (output storage)
        ├── graph.png
        └── report.pdf

templates/
├── assessment.html (Section 1 form)
├── screening.html (Section 2 form)
├── assessment2.html (Section 3 form)
├── final_analysis.html (aggregated results)
├── dashboard.html (progress tracking)
├── home.html (entry point)
└── base_sidebar.html (common UI)

static/ (CSS and JS)
├── assessment.css
├── screening.css
├── assessment2.css
├── final_analysis.css
└── index.js
```

## Video Analysis Package Files in Detail

### `videoanalysis/pose_detector.py`
- **Purpose**: Detects human pose landmarks from video frames
- **Key Function**: `detect_pose(frame)` 
  - Loads MediaPipe Pose Landmarker from `pose_landmarker_full.task`
  - Converts OpenCV BGR frame to MediaPipe RGB
  - Returns 33 pose landmark coordinates (nose, eyes, shoulders, elbows, wrists, hips, knees, ankles)
  - Handles frame-by-frame detection for video processing

### `videoanalysis/scoring.py`
- **Purpose**: Computes behavioral metrics from detected pose landmarks
- **Key Metrics**:
  - `eye_contact`: Symmetry of nose relative to left and right eyes (0-100)
  - `face_direction`: Frontal alignment score (0-100)
  - `head_pose`: Vertical alignment of eyes (0-100)
  - `body_posture`: Shoulder height difference (0-100)
  - `movement`: Wrist velocity across sampled frames (0-100)
  - `attention`: Average of face direction and head pose (0-100)
  - `asd_score`: Overall behavioral score (average of attention, posture, movement)
  - `risk`: Classification as Low (>70), Moderate (>40), or High (≤40)

### `videoanalysis/video_processor.py`
- **Purpose**: Orchestrates the video analysis pipeline
- **Workflow**:
  1. Opens video file with OpenCV
  2. Extracts total frame count and video properties
  3. Samples every 5th frame to reduce computation
  4. For each sampled frame:
     - Detect pose landmarks
     - Calculate behavior scores
     - Accumulate arrays for graphing
  5. Averages all frame-level scores
  6. Returns aggregated results and frame arrays
- **Output**: Dictionary with keys like `eye_scores[]`, `attention_scores[]`, `movement_scores[]`, `overall_risk`, `summary_text`

### `videoanalysis/report_generator.py`
- **Purpose**: Creates visual graph representation of behavior metrics
- **Graph Features**:
  - Plots frame-by-frame scores for eye contact, attention, and movement
  - Overlays shaded risk zones:
    - Green: Low risk (>70)
    - Yellow: Moderate risk (40-70)
    - Red: High risk (<40)
  - Adds labels, legends, and axis titles
  - Saves as `videoanalysis/static/graph.png` for embedding in reports
- **Dependencies**: Matplotlib

### `videoanalysis/pdf_report.py`
- **Purpose**: Generates professional PDF report for healthcare providers
- **Report Contents**:
  - Title and timestamp
  - Overall ASD behavioral risk classification
  - Key metrics: eye contact, attention, movement scores
  - Risk interpretation and clinical notes
  - Embedded frame-by-frame behavior graph
  - Disclaimers: "For screening purposes only, not a clinical diagnosis"
  - Instructions for next steps
- **Storage**: Saves to `videoanalysis/static/report.pdf`
- **Dependencies**: ReportLab

### `videoanalysis/pose_landmarker_full.task`
- **Purpose**: Pre-trained MediaPipe Pose Landmarker model asset
- **Specification**: Full-body pose detection with 33 keypoints
- **Usage**: Loaded by `pose_detector.py` to enable real-time landmark detection
- **Format**: TensorFlow Lite model (.task)

## Models and Expected Inputs

### `section1_model.pkl`
Used by Session 1 with features such as:
- `Age_Years`
- `Speech Delay/Language Disorder`
- `Learning disorder`
- `Genetic_Disorders`
- `Global developmental delay/intellectual disability`
- `Family_mem_with_ASD`
- `Jaundice`
- `Depression`
- `Anxiety_disorder`
- **Loaded in**: `main.py` at startup
- **Route**: `/assessment` and `/submit`

### `section2_model.pkl`
Used by Session 2 with features:
- `A1` through `A9`
- `A10_Autism_Spectrum_Quotient`
- **Loaded in**: `main.py` at startup
- **Route**: `/screening` and `/submit`

### `section3_model.pkl`
Used by Session 3 with features:
- `Childhood Autism Rating Scale`
- `Social_Responsiveness_Scale`
- `Social/Behavioural Issues`
- `Anxiety_disorder`
- `Depression`
- `Age_Years`
- `Sex`
- **Loaded in**: `main.py` at startup
- **Route**: `/assessment2` and `/submit`

### `dreamdataset_model.pkl`
Optional standalone demo model loaded by `app.py` only.
- Not used in the main three-session workflow
- Available for legacy demo purposes only

## How Final Analysis Combines All Sessions

The `/final_analysis` route in `main.py` works as follows:

1. **Retrieves Latest Results from MySQL**
   - Session 1 (Assessment) latest result via `db.py`
   - Session 2 (Screening) latest result via `db.py`
   - Session 3 (Observation) latest result via `db.py`
   - Session 4 (Video Analysis) latest result if available

2. **Extracts Individual Session Scores**
   - Session 1 risk level + probability
   - Session 2 autism trait score + probability
   - Session 3 behavioral risk + probability
   - Video Analysis risk classification (if completed)

3. **Combines Results**
   - Calculates weighted composite score
   - Generates combined risk interpretation
   - Considers all four data streams for holistic assessment

4. **Presents in `templates/final_analysis.html`**
   - Displays scores from each session
   - Shows overall ASD screening recommendation
   - Provides clinical next steps
   - Includes video analysis findings if available

5. **Database Logging**
   - Stores final analysis timestamp and results in `screening_history`
   - Maintains complete audit trail for healthcare providers

## Usage

1. Activate the virtual environment:

```powershell
venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r videoanalysis/requirements.txt
pip install pandas mysql-connector-python scikit-learn
```

3. Ensure the model files are present:
- `section1_model.pkl`
- `section2_model.pkl`
- `section3_model.pkl`
- `dreamdataset_model.pkl` (optional for `app.py`)

4. Run the main app:

```bash
python main.py
```

5. Visit:

```text
http://127.0.0.1:5000/
```

## Notes

- The main final analysis is based on the three tabular sections.
- Video analysis is supplemental and provides additional behavior insight.
- `main.py` saves results in MySQL and computes overall risk from the latest saved section entries.
