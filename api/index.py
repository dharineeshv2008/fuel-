from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
import os
import io
import csv
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'master_majestic_50_key_2026')

# --- Database Setup (SQLite for analytics) ---
DB_FILE = 'analytics.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            distance REAL,
            fuel_required REAL,
            total_cost REAL,
            currency TEXT,
            trip_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB (Note: Filesystem is read-only on Vercel, but we keep the logic for local/stable environments)
try:
    init_db()
except Exception:
    pass

# --- Helper Functions ---
def safe_float(value, default=None):
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default

def get_efficiency(mileage):
    if mileage >= 25: return "Excellent"
    if mileage >= 18: return "Good"
    if mileage >= 12: return "Average"
    return "Poor"

# --- Main Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # --- [1] Core Inputs (1-10) ---
        dist_val = safe_float(request.form.get('distance'))
        mileage = safe_float(request.form.get('mileage'))
        f_price = safe_float(request.form.get('fuel_price'))
        unit = request.form.get('unit', 'km')
        currency = request.form.get('currency', '₹')
        trip_type = request.form.get('trip_type', 'one-way')
        
        # Reverse Calculation (Budget -> Distance)
        budget = safe_float(request.form.get('budget'))
        reverse_dist = (budget / f_price) * mileage if budget and f_price and mileage else None

        # Multi-stop logic
        stops_dist = safe_float(request.form.get('stops_distance'), 0)

        # Validation
        if not budget and (dist_val is None or dist_val <= 0):
            flash("Please enter a valid Distance or Budget.")
            return redirect(url_for('index'))
        if mileage is None or mileage <= 0:
            flash("Mileage must be greater than zero.")
            return redirect(url_for('index'))

        # Distance logic
        effective_dist = dist_val if dist_val else reverse_dist
        if trip_type == 'round-trip':
            total_dist = effective_dist * 2
        elif trip_type == 'multi-city':
            total_dist = effective_dist + stops_dist
        else:
            total_dist = effective_dist

        # Core results
        fuel_req = total_dist / mileage
        total_trip_cost = fuel_req * f_price
        cost_per_unit = total_trip_cost / total_dist if total_dist > 0 else 0

        # --- [2] Financial IQ (11-20) ---
        daily_commute = safe_float(request.form.get('daily_commute'), 0)
        inflation = safe_float(request.form.get('inflation'), 0) / 100
        passengers = safe_float(request.form.get('passengers'), 1)
        
        monthly_cost = (daily_commute * 30 / mileage) * f_price
        yearly_cost = (daily_commute * 365 / mileage) * f_price
        cost_split = total_trip_cost / passengers if passengers > 0 else total_trip_cost
        
        # 5-Year Projection with Inflation
        five_year_projection = 0
        current_f_price = f_price
        for i in range(5):
            current_f_price *= (1 + inflation)
            five_year_projection += (daily_commute * 365 / mileage) * current_f_price

        # --- [3] Comparison Engine (21-30) ---
        compare_data = {}
        # Petrol vs Diesel
        p_p = safe_float(request.form.get('petrol_price'))
        d_p = safe_float(request.form.get('diesel_price'))
        if p_p and d_p:
            p_cost = (total_dist / mileage) * p_p
            d_cost = (total_dist / mileage) * d_p
            compare_data['fuel'] = {'cheaper': 'Petrol' if p_cost < d_cost else 'Diesel', 'savings': abs(p_cost - d_cost)}

        # EV Simulation
        ev_kwh_per_dist = 0.15 # Avg kWh per km
        ev_price_kwh = safe_float(request.form.get('ev_price'), 8) # Def 8 per kWh
        ev_trip_cost = total_dist * ev_kwh_per_dist * ev_price_kwh
        compare_data['ev_savings'] = total_trip_cost - ev_trip_cost

        # CNG Simulation
        cng_price = f_price * 0.75 # Avg CNG is ~25% cheaper
        cng_mileage = mileage * 1.2 # CNG has slightly better mileage
        cng_trip_cost = (total_dist / cng_mileage) * cng_price
        compare_data['cng_cost'] = round(cng_trip_cost, 2)

        # Hybrid Simulation
        hybrid_mileage = mileage * 1.5 # Hybrid ~50% better
        hybrid_trip_cost = (total_dist / hybrid_mileage) * f_price
        compare_data['hybrid_cost'] = round(hybrid_trip_cost, 2)

        # --- [4] Eco Analytics ---
        co2_factor = 2.31 # kg per L for Petrol
        total_co2 = fuel_req * co2_factor

        # --- [5] Results Packaging ---
        results = {
            'distance': round(total_dist, 2),
            'unit': unit,
            'fuel_req': round(fuel_req, 2),
            'total_cost': round(total_trip_cost, 2),
            'cost_per_unit': round(cost_per_unit, 2),
            'currency': currency,
            'monthly': round(monthly_cost, 2),
            'yearly': round(yearly_cost, 2),
            'split': round(cost_split, 2),
            'five_year': round(five_year_projection, 2),
            'efficiency': get_efficiency(mileage),
            'co2': round(total_co2, 2),
            'comparison': compare_data,
            'ev_cost': round(ev_trip_cost, 2),
            'trip_display': trip_type.replace('-', ' ').title()
        }

        # SQLite Persistence (Try block because Vercel is read-only)
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO history (timestamp, distance, fuel_required, total_cost, currency, trip_type) VALUES (?, ?, ?, ?, ?, ?)',
                         (datetime.now().strftime('%Y-%m-%d %H:%M'), total_dist, fuel_req, total_trip_cost, currency, trip_type))
            conn.commit()
            conn.close()
        except:
            pass

        return render_template('index.html', results=results)

    except Exception as e:
        app.logger.error(f"Logic Error: {str(e)}")
        flash("Strategic analysis failed. Ensure all quantitative metrics are valid.")
        return redirect(url_for('index'))

# --- Reporting Routes (CSV/PDF) ---
@app.route('/export/csv', methods=['POST'])
def export_csv():
    data = request.form.to_dict()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Metric', 'Value'])
    for key, value in data.items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=fuel_report.csv"}
    )

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    data = request.form.to_dict()
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "MAJESTIC FUEL ANALYSIS REPORT")
    p.setFont("Helvetica", 12)
    y = 700
    for key, value in data.items():
        p.drawString(100, y, f"{key.replace('_', ' ').title()}: {value}")
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="fuel_report.pdf", mimetype='application/pdf')

@app.route('/report', methods=['POST'])
def report_view():
    data = request.form.to_dict()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('report.html', results=data, timestamp=timestamp)

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

# Entrypoint for Vercel
app = app
if __name__ == '__main__':
    app.run(debug=True)
