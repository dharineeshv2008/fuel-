from flask import Flask, render_template, request, redirect, url_for, flash
import os

# Important: We tell Flask to look for templates and static in parents
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', 'vercel_premium_key_123')

# --- Helper Functions ---
def safe_float(value, default=None):
    """Safely converts a string to a float, returning default if invalid or empty."""
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default

@app.route('/')
def index():
    """Renders the premium dashboard."""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    """Handles fuel calculations with robust validation."""
    try:
        # 1. Capture Inputs defensively
        distance = safe_float(request.form.get('distance'))
        mileage = safe_float(request.form.get('mileage'))
        fuel_price = safe_float(request.form.get('fuel_price'))
        
        trip_type = request.form.get('trip_type', 'one-way')
        currency = request.form.get('currency', '₹')
        
        # Capture Comparison Extras (Optional)
        p_price_raw = request.form.get('petrol_price', '')
        d_price_raw = request.form.get('diesel_price', '')

        # 2. Server-side Validation
        errors = []
        if distance is None: errors.append("Invalid or missing distance.")
        elif distance <= 0: errors.append("Distance must be a positive number.")
        
        if mileage is None: errors.append("Invalid or missing mileage.")
        elif mileage <= 0: errors.append("Mileage must be greater than zero.")
        
        if fuel_price is None: errors.append("Invalid or missing fuel price.")
        elif fuel_price <= 0: errors.append("Fuel price must be a positive number.")

        if errors:
            for err in errors: flash(err)
            return redirect(url_for('index'))

        # 3. Core Calculations
        calc_dist = distance * 2 if trip_type == 'round-trip' else distance
        fuel_req = calc_dist / mileage
        total_cost = fuel_req * fuel_price
        monthly_cost = (calc_dist * 30 / mileage) * fuel_price

        # 4. Fuel Comparison logic
        comparison = None
        p_p = safe_float(p_price_raw)
        d_p = safe_float(d_price_raw)
        
        if p_p is not None and d_p is not None:
            if p_p > 0 and d_p > 0:
                p_c = (calc_dist / mileage) * p_p
                d_c = (calc_dist / mileage) * d_p
                comparison = {
                    'petrol_cost': p_c,
                    'diesel_cost': d_c,
                    'cheaper': "Petrol" if p_c < d_c else "Diesel",
                    'difference': abs(p_c - d_c)
                }

        # 5. Package results
        results = {
            'fuel_required': round(fuel_req, 2),
            'total_cost': total_cost,
            'monthly_cost': monthly_cost,
            'currency': currency,
            'trip_type': trip_type.replace('-', ' ').title(),
            'comparison': comparison
        }
        
        return render_template('index.html', results=results)

    except Exception as e:
        app.logger.error(f"System Error: {str(e)}")
        flash("A system error occurred. Please try again.")
        return redirect(url_for('index'))

@app.route('/reset')
def reset():
    return redirect(url_for('index'))

# Export app for Vercel
app = app
