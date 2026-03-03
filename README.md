# Fuel Expense Calculator (Production Ready)

A professional full-stack web application designed for quick fuel calculations and comparison, optimized for Python-supported cloud hosting.

## 🚀 Why Netlify Failed?
Netlify is a **static hosting** platform. It specializes in serving HTML, CSS, and Client-side JavaScript. It does not provide a **Python Runtime** to execute Flask backend code. To run a Flask app, you need a platform that supports persistent server processes, like **Render.com**.

## 🛠 Features
- **Trip Calculation**: One-way or Round-trip.
- **Monthly Budget**: Automatic 30-day expense projection.
- **Fuel Comparison**: Petrol vs Diesel cost analysis.
- **Production UI**: Modern fintech theme with zero JavaScript.
- **Server-side Validation**: Robust error handling for invalid/negative inputs.

## 📦 Deployment Instructions (Render.com)

1. **Create a Render Account**: Sign up at [render.com](https://render.com).
2. **Connect GitHub/GitLab**: Push your rectified project to a repository.
3. **Create a New Web Service**:
   - Select your repository.
   - **Name**: `fuel-expense-calculator`
   - **Environment**: `Python 3`
   - **Region**: Select closest to you.
   - **Branch**: `main`
4. **Configure Build & Start**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. **Environment Variables**:
   - Create a `SECRET_KEY` variable for production security.
6. **Deploy**: Render will automatically build and serve your Flask app.

## 📂 Project Structure
```text
fuel-expense-calculator/
├── app.py              # Main Flask Entry Point
├── requirements.txt    # Dependencies (Flask + Gunicorn)
├── static/
│   └── style.css       # Professional Dashboard CSS
├── templates/
│   └── index.html      # Jinja2 Main Dashboard
└── README.md           # Documentation & Deployment Guide
```

## 🛠 Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python app.py
```
*Note: Debug mode is OFF for production safety.*
