from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
import os
import io
import csv
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'friendly_majestic_key_2026')

# --- Database Setup (SQLite for Vehicle Profiles and History) ---
DB_FILE = 'fuel_data.db'

def get_db_connection():
    # Note: SQLite writes might fail on Vercel's read-only filesystem.
    # We use a try-except layer in route handlers to ensure the app doesn't crash.
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        # History Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                distance REAL,
                total_cost REAL,
                currency TEXT
            )
        ''')
        # Vehicle Profiles Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS vehicle_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                mileage REAL
            )
        ''')
        conn.commit()
        conn.close()
    except Exception:
        pass

# Initialize on startup
init_db()

# --- Helper Functions ---
def safe_float(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    try:
        # Remove any non-numeric characters like commas if they slipped in
        clean_val = str(value).replace(',', '').strip()
        return float(clean_val)
    except (ValueError, TypeError):
        return default

def get_affordability_color(total_cost):
    """Determines color based on cost thresholds (Beginner Friendly)"""
    if total_cost < 500: return "color-low" # Green
    if total_cost < 2000: return "color-mid" # Orange
    return "color-high" # Red

def get_efficiency_rating(mileage):
    if mileage >= 25: return "Super Efficient! 🍃"
    if mileage >= 18: return "Great Mileage! ✨"
    if mileage >= 12: return "Average Economy 🚗"
    return "Heavy Fuel Consumer ⛽"

# --- Main Routes ---
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        profiles = conn.execute('SELECT * FROM vehicle_profiles').fetchall()
        history = conn.execute('SELECT * FROM calculations ORDER BY id DESC LIMIT 5').fetchall()
        conn.close()
    except Exception:
        profiles = []
        history = []
    
    return render_template('index.html', profiles=profiles, history=history)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Capture Inputs
        distance = safe_float(request.form.get('distance'))
        mileage = safe_float(request.form.get('mileage'))
        fuel_price = safe_float(request.form.get('fuel_price'))
        currency = request.form.get('currency', '₹')
        trip_type = request.form.get('trip_type', 'one-way')
        
        # Friendly Validation Messages
        errors = []
        if distance is None or distance <= 0:
            errors.append("Please enter how far you're planning to travel.")
        if mileage is None or mileage <= 0:
            errors.append("We need your vehicle's mileage to calculate fuel use.")
        if fuel_price is None or fuel_price <= 0:
            errors.append("Please provide the current fuel price per litre.")

        if errors:
            for err in errors: flash(err)
            return redirect(url_for('index'))

        # Calculations
        actual_distance = distance * 2 if trip_type == 'round-trip' else distance
        fuel_needed = actual_distance / mileage
        total_cost = fuel_needed * fuel_price
        
        # Monthly/Yearly Projections (Simple Daily Commute)
        daily_km = safe_float(request.form.get('daily_commute'), 0)
        monthly_cost = (daily_km * 30 / mileage) * fuel_price if daily_km > 0 else 0
        yearly_cost = (daily_km * 365 / mileage) * fuel_price if daily_km > 0 else 0

        # Petrol vs Diesel Comparison (Optional)
        p_price = safe_float(request.form.get('petrol_price'))
        d_price = safe_float(request.form.get('diesel_price'))
        comparison = None
        if p_price and d_price:
            p_cost = (actual_distance / mileage) * p_price
            d_cost = (actual_distance / mileage) * d_price
            comparison = {
                'cheaper': "Petrol" if p_cost < d_cost else "Diesel",
                'difference': abs(p_cost - d_cost)
            }

        # Eco Impact
        co2_emissions = fuel_needed * 2.31 # Average kg per Litre

        results = {
            'fuel_needed': round(fuel_needed, 2),
            'total_cost': round(total_cost, 2),
            'monthly_cost': round(monthly_cost, 2),
            'yearly_cost': round(yearly_cost, 2),
            'currency': currency,
            'color': get_affordability_color(total_cost),
            'rating': get_efficiency_rating(mileage),
            'actual_distance': actual_distance,
            'comparison': comparison,
            'co2': round(co2_emissions, 2)
        }

        # Save History (Try-Except for Vercel)
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO calculations (timestamp, distance, total_cost, currency) VALUES (?, ?, ?, ?)',
                         (datetime.now().strftime('%Y-%m-%d %H:%M'), actual_distance, total_cost, currency))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return render_template('index.html', results=results)

    except Exception:
        flash("Something went wrong with the calculation. Please check your numbers!")
        return redirect(url_for('index'))

@app.route('/save-vehicle', methods=['POST'])
def save_vehicle():
    name = request.form.get('v_name')
    mileage = safe_float(request.form.get('v_mileage'))
    if name and mileage:
        try:
            conn = get_db_connection()
            conn.execute('INSERT OR REPLACE INTO vehicle_profiles (name, mileage) VALUES (?, ?)', (name, mileage))
            conn.commit()
            conn.close()
            flash(f"Vehicle '{name}' saved successfully!")
        except Exception:
            flash("Could not save vehicle info at this time.")
    return redirect(url_for('index'))

@app.route('/export/csv', methods=['POST'])
def export_csv():
    data = request.form.to_dict()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Calculation Metric', 'Estimated Value'])
    for key, val in data.items():
        writer.writerow([key.replace('_', ' ').capitalize(), val])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=fuel_plan.csv"}
    )

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    data = request.form.to_dict()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, 750, "Fuel Planning Summary")
    p.setFont("Helvetica", 12)
    y = 700
    p.drawString(100, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 40
    for key, val in data.items():
        p.drawString(100, y, f"{key.replace('_', ' ').capitalize()}: {val}")
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="fuel_report.pdf", mimetype='application/pdf')

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

# Export app for Vercel
app = app
