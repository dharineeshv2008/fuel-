from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
# Production security: Use environment secret or fallback
app.secret_key = os.environ.get('SECRET_KEY', 'premium_fuel_key_998877')

# Database Configuration
db_path = os.path.join(os.path.dirname(__file__), 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Model ---
class FuelCalculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    distance = db.Column(db.Float, nullable=False)
    mileage = db.Column(db.Float, nullable=False)
    fuel_price = db.Column(db.Float, nullable=False)
    fuel_required = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), nullable=False)
    trip_type = db.Column(db.String(20), nullable=False)

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
    """Renders the premium dashboard with history."""
    try:
        history = FuelCalculation.query.order_by(FuelCalculation.timestamp.desc()).limit(10).all()
        return render_template('index.html', history=history)
    except Exception as e:
        app.logger.error(f"Error loading history: {str(e)}")
        return render_template('index.html', history=[])

@app.route('/calculate', methods=['POST'])
def calculate():
    """Handles fuel calculations with robust validation and history storage."""
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

        # 2. Server-side Validation with Specific Feedback
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

        # 3. Trip Logic
        calc_distance = distance * 2 if trip_type == 'round-trip' else distance
        
        # 4. Core Calculations (Mileage > 0 is guaranteed by validation)
        fuel_req = calc_distance / mileage
        total_cost = fuel_req * fuel_price
        
        # 5. Monthly Projection (30 Days)
        monthly_cost = (calc_distance * 30 / mileage) * fuel_price

        # 6. Fuel Comparison logic (Only if both are provided and valid)
        comparison = None
        p_p = safe_float(p_price_raw)
        d_p = safe_float(d_price_raw)
        
        if p_p is not None and d_p is not None:
            if p_p > 0 and d_p > 0:
                p_c = (calc_distance / mileage) * p_p
                d_c = (calc_distance / mileage) * d_p
                comparison = {
                    'petrol_cost': p_c,
                    'diesel_cost': d_c,
                    'cheaper': "Petrol" if p_c < d_c else "Diesel",
                    'difference': abs(p_c - d_c)
                }

        # 7. Save to Database
        try:
            calc_entry = FuelCalculation(
                distance=calc_distance,
                mileage=mileage,
                fuel_price=fuel_price,
                fuel_required=fuel_req,
                total_cost=total_cost,
                currency=currency,
                trip_type=trip_type
            )
            db.session.add(calc_entry)
            db.session.commit()
        except Exception as db_err:
            app.logger.error(f"Database Error: {str(db_err)}")
            db.session.rollback()

        # 8. Render with Results
        history = FuelCalculation.query.order_by(FuelCalculation.timestamp.desc()).limit(10).all()
        results = {
            'fuel_required': round(fuel_req, 2),
            'total_cost': total_cost,
            'monthly_cost': monthly_cost,
            'currency': currency,
            'trip_type': trip_type.replace('-', ' ').title(),
            'comparison': comparison
        }
        
        return render_template('index.html', results=results, history=history)

    except Exception as e:
        app.logger.error(f"System Error: {str(e)}")
        flash("A system error occurred. Please check your inputs and try again.")
        return redirect(url_for('index'))

@app.route('/reset')
def reset():
    """Safety route to clear form and redirect home."""
    return redirect(url_for('index'))

@app.route('/clear-history')
def clear_history():
    """Clear all records for privacy."""
    try:
        db.session.query(FuelCalculation).delete()
        db.session.commit()
    except Exception as e:
        app.logger.error(f"History Clear Error: {str(e)}")
        db.session.rollback()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Debug mode OFF for production safety
    app.run(debug=False)

@app.route('/reset')
def reset():
    """Safety route to clear form and redirect home."""
    return redirect(url_for('index'))

@app.route('/clear-history')
def clear_history():
    """Optional: Clear all records for privacy."""
    try:
        db.session.query(FuelCalculation).delete()
        db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Debug mode OFF for production safety
    app.run(debug=False)
