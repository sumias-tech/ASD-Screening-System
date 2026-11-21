# 🧠 Attention & Movement Tracking API

A full-stack web application built with Flask and Google's MediaPipe that analyzes video files to track human attention and repetitive motor behaviors. It processes video frames, calculates complex body pose metrics, and generates comprehensive PDF reports with data visualizations.

## ✨ Key Features

* **True Relative Attention Tracking:** Uses facial landmark geometry (yaw and pitch) to determine eye contact and attention, calculating facial symmetry rather than absolute screen position.
* **2D Repetitive Movement Detection:** Tracks wrist velocity across both X and Y axes using trigonometric distance (`math.hypot`) to detect rapid, repetitive movements (stimming).
* **Automated PDF Reporting:** Generates clinical-style PDF reports complete with Matplotlib data visualizations showing attention and movement scores over the duration of the video.
* **Web UI:** A clean, user-friendly frontend for uploading videos and instantly downloading the resulting analysis.

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Computer Vision:** OpenCV, Google MediaPipe (Pose Landmarker)
* **Data Visualization & Reporting:** Matplotlib, ReportLab
* **Frontend:** HTML/CSS (Jinja2 Templates)

## 🏃‍♂️ Installation & Setup Guide

### Prerequisites
1. **Python (3.8 or newer):** Download from [python.org](https://www.python.org/downloads/). 
   * *Windows Users:* Ensure you check **"Add Python to PATH"** during installation.
2. **Git:** Download from [git-scm.com](https://git-scm.com/).

### 1. Clone the Repository
```bash
git clone [https://github.com/benjaminfranglin/asd-movement-tracker.git](https://github.com/benjaminfranglin/asd-movement-tracker.git)
cd asd-movement-tracker
