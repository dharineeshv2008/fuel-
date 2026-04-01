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

Follow these steps to get the Fuel Expense Calculator running on your local machine.

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package installer)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/dharineeshv2008/fuel-.git
cd fuel-expense-calculator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Professional applications use environment variables for sensitive data. 

1. Copy the example environment file:
   ```bash
   cp .env.example .env  # On Windows: copy .env.example .env
   ```
2. Open `.env` and configure your `FLASK_SECRET_KEY`. You can generate a random key with:
   ```bash
   python -c "import secrets; print(secrets.token_hex())"
   ```

### 3. Running Locally

We provide a dedicated `run.py` script for a seamless local hosting experience:

```bash
python run.py
```

Navigate to: **`http://localhost:5000`** in your browser.

---

## 🛠️ Advanced Usage

### Local Hosting with Gunicorn
For a more production-like environment on Linux/Mac, you can use Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Secret key for session encryption | (Development key) |
| `PORT` | The port to run the application on | `5000` |
| `FLASK_DEBUG` | Enable/Disable Flask debug mode | `1` (Enabled) |

---

## ☁️ Deployment to Vercel

The project remains fully compatible with Vercel:
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in the project root.
3. Vercel will use `api/index.py` and `vercel.json` for serverless deployment.

---

## ⚠️ Data Persistence Warning

Because this project complies with strict **"No Database"** and **"No JavaScript (No localStorage)"** rules, all user data (vehicles, history, preferences) is saved securely in the **Flask Session Cookie**.

**If you close your browser or clear cookies, your saved vehicles and history log will reset.**

---

## 📄 License
MIT License — feel free to use and modify.
