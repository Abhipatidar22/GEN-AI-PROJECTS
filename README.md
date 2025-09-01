# AI Life Coach (Flask)

A minimal, fully working demo of an AI-driven personalized life coaching assistant built with **Flask**, **HTML**, and **CSS**.  
It implements the workflow from the PDF: user registration/login, journals, mood check-ins, simple NLP (rule-based sentiment & intent), personalization, coaching suggestions, progress tracking, and a lightweight dashboard.

## Features
- User registration & login (session-based)
- Journals with mood (+ simple sentiment & intent classification)
- Goals (CRUD + progress)
- Daily coaching session with recommendations
- Lightweight dashboard with inline SVG mood trend graph (no external JS libs needed)
- SQLite database auto-initialized on first run with **dummy data**
- No external APIs required

## Quickstart
1. **Create & activate a virtual environment (optional but recommended):**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open your browser:**  
   http://127.0.0.1:5000

5. **Demo login:**  
   - Email: `demo@coach.app`  
   - Password: `demo123`

> The app auto-creates `app.db` and seeds demo content on first launch.

## Project Structure
```
ai_life_coach_app/
├─ app.py
├─ recommender.py
├─ utils.py
├─ requirements.txt
├─ README.md
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ dashboard.html
│  ├─ journal.html
│  ├─ goals.html
│  ├─ coaching.html
│  ├─ login.html
│  ├─ register.html
│  └─ privacy.html
└─ static/
   ├─ css/style.css
   └─ js/app.js
```

## Notes
- Passwords are hashed with SHA256 for this demo. In production use a stronger password hasher.
- This is a teaching/demo project and **not** a replacement for professional mental health services.
