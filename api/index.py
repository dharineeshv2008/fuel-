from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'majestic_fintech_secure_key_2026')

# --- Helper Functions ---
def safe_float(value, default=None):
    """Safely converts a string to a float, returning default if invalid or empty."""
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default

def get_efficiency_rating(mileage):
    """Returns an efficiency rating based on mileage."""
    if mileage >= 25: return "Excellent"
    if mileage >= 18: return "Good"
    if mileage >= 12: return "Average"
    return "Poor"

@app.route('/')
def index():
    """Renders the Majestic Dashboard."""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    """Handles advanced fuel calculations with multi-city and projections."""
    try:
        # 1. Capture Primary Inputs
        dist = safe_float(request.form.get('distance'))
        mileage = safe_float(request.form.get('mileage'))
        f_price = safe_float(request.form.get('fuel_price'))
        
        trip_type = request.form.get('trip_type', 'one-way')
        currency = request.form.get('currency', '₹')
        
        # Capture Multi-city Additional Stops
        stops_dist = safe_float(request.form.get('stops_distance'), 0)
        
        # Capture Comparison Engine Inputs (Optional)
        p_p_raw = request.form.get('petrol_price', '')
        d_p_raw = request.form.get('diesel_price', '')

        # 2. Defensive Validation
        errors = []
        if dist is None or dist <= 0: errors.append("Valid distance is required.")
        if mileage is None or mileage <= 0: errors.append("Valid mileage is required.")
        if f_price is None or f_price <= 0: errors.append("Valid fuel price is required.")

        if errors:
            for err in errors: flash(err)
            return redirect(url_for('index'))

        # 3. Smart Trip Mode Logic
        total_dist = dist
        if trip_type == 'round-trip':
            total_dist = dist * 2
        elif trip_type == 'multi-city':
            total_dist = dist + stops_dist
            
        # 4. Core Metrics
        fuel_req = total_dist / mileage
        total_cost = fuel_req * f_price
        
        # 5. Projections (Daily Commute based)
        daily_commute = safe_float(request.form.get('daily_commute'), 0)
        monthly_cost = (daily_commute * 30 / mileage) * f_price if daily_commute > 0 else 0
        yearly_cost = (daily_commute * 365 / mileage) * f_price if daily_commute > 0 else 0

        # 6. Fuel Efficiency Analyzer
        efficiency = get_efficiency_rating(mileage)

        # 7. Petrol vs Diesel Comparison Engine
        comparison = None
        p_p = safe_float(p_p_raw)
        d_p = safe_float(d_p_raw)
        
        if p_p is not None and d_p is not None and p_p > 0 and d_p > 0:
            p_c = (total_dist / mileage) * p_p
            d_c = (total_dist / mileage) * d_p
            cheaper = "Petrol" if p_c < d_c else "Diesel"
            comparison = {
                'petrol_cost': p_c,
                'diesel_cost': d_c,
                'cheaper': cheaper,
                'difference': abs(p_c - d_c)
            }

        # 8. Package Majestic Results
        results = {
            'distance': round(total_dist, 2),
            'fuel_required': round(fuel_req, 2),
            'total_cost': total_cost,
            'monthly_cost': monthly_cost,
            'yearly_cost': yearly_cost,
            'efficiency': efficiency,
            'currency': currency,
            'trip_type_display': trip_type.replace('-', ' ').title(),
            'comparison': comparison
        }
        
        return render_template('index.html', results=results)

    except Exception as e:
        app.logger.error(f"Majestic Error: {str(e)}")
        flash("Analysis failed. Please check your quantitative inputs.")
        return redirect(url_for('index'))

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

# Entrypoint for Vercel
app = app
