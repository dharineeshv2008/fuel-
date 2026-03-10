# Fuel Cost Calculator — Python Edition

A simple, robust, **Python-only** web application that helps you calculate fuel expenses, plan trips, and track vehicle costs without a database.

**Note:** This application intentionally uses zero client-side JavaScript to maximize backend reliability and simplicity. All data is persisted temporarily in your browser session cookie.

---

## ✨ Features (Powered by Python & Flask)

### 🧮 Fuel Calculator
- Distance-based fuel cost
- Round-trip support
- Cost per km & per passenger
- Fuel efficiency rating & CO₂ emissions
- Monthly & yearly budget projections
- Budget alerts

### 🗺️ Trip Planner
- Long-distance route estimation
- Fuel stop planning based on tank size
- Travel time estimation

### 📝 Fuel Logging & History
- Daily fuel purchase logging
- Odometer tracking
- Saved calculation history

### 🚗 Vehicle Management
- Add & remove vehicle profiles
- Auto-fill calculations using session state

### ⚙️ Settings
- 🌙 Dark / Light mode saving (via Flask Session)
- Currency customization
- Default fuel price

---

## 📦 Tech Stack (Strictly Enforced)

| Layer      | Technology            |
|------------|-----------------------|
| Backend    | Python Flask          |
| Logic      | Pure Python (`utils.py`) |
| Frontend   | HTML5 + CSS3 + Jinja2 |
| Icons      | FontAwesome 6         |
| Storage    | Flask Session Cookie  |

**What is NOT used:**
- No JavaScript (React, Vue, Vanilla JS)
- No Databases (SQLite, MySQL)
- No CSS Frameworks (Bootstrap, Tailwind)

---

## 📂 Architecture

```
fuel-expense-calculator/
├── app.py                  # Flask server & Routing logic
├── utils.py                # Core Python calculation formulas
├── requirements.txt        # Python dependencies
├── README.md               # This documentation
├── templates/              # Jinja2 HTML Templates
│   ├── base.html           # Main layout shell
│   ├── index.html          # Dashboard rendering
│   ├── calculator.html     # Fuel Form & Results
│   ├── trip.html           # Trip planning & stops
│   ├── history.html        # Logs and calc history
│   ├── vehicles.html       # Session-based vehicles
│   └── settings.html       # Theme configuration
└── static/css/
    └── style.css           # Glassmorphism Design System
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.7+

### Installation & Execution

```bash
# 1. Clone the repository
git clone https://github.com/dharineeshv2008/fuel-.git
cd fuel-expense-calculator

# 2. Install Flask
pip install flask

# 3. Run the application
python app.py
```

### Open in browser
Navigate to: `http://localhost:5000`

### ☁️ Deploying to Vercel
The project is completely configured for Vercel Serverless Functions out of the box.
1. Create a free account on [Vercel](https://vercel.com/)
2. Install the Vercel CLI: `npm i -g vercel`
3. Run the following command in the project root:
```bash
vercel
```
Vercel will detect the `vercel.json` and deploy your Flask app seamlessly.

---

## ⚠️ Data Persistence Warning

Because this project complies with strict **"No Database"** and **"No JavaScript (No localStorage)"** rules, all user data (vehicles, history, preferences) is saved securely in the **Flask Session Cookie**.

**If you close your browser or clear cookies, your saved vehicles and history log will reset.**

---

## 📄 License
MIT License — feel free to use and modify.
