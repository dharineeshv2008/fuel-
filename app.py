from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
# Secure secret key for production
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key_12345')

@app.route('/')
def index():
    """Renders the main dashboard."""
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    """Handles fuel calculation and comparison logic."""
    try:
        # 1. Get and sanitize inputs from form
        distance = float(request.form.get('distance', 0))
        mileage = float(request.form.get('mileage', 0))
        fuel_price = float(request.form.get('fuel_price', 0))
        trip_type = request.form.get('trip_type', 'one-way')
        currency = request.form.get('currency', '₹')
        
        # 2. Server-side Validation
        if distance <= 0:
            flash("Distance must be a positive number.")
            return redirect(url_for('index'))
        if mileage <= 0:
            flash("Mileage must be greater than zero.")
            return redirect(url_for('index'))
        if fuel_price <= 0:
            flash("Fuel price must be a positive number.")
            return redirect(url_for('index'))

        # 3. Trip Logic (Round-trip doubling)
        calc_distance = distance * 2 if trip_type == 'round-trip' else distance
        
        # 4. Core Calculations
        fuel_required = calc_distance / mileage
        total_cost = fuel_required * fuel_price
        
        # 5. Monthly Budget (30-day projection)
        monthly_cost = (calc_distance * 30 / mileage) * fuel_price

        # 6. Fuel Comparison Mode (Optional)
        petrol_price = request.form.get('petrol_price')
        diesel_price = request.form.get('diesel_price')
        comparison = None
        
        if petrol_price and diesel_price:
            try:
                p_price = float(petrol_price)
                d_price = float(diesel_price)
                if p_price > 0 and d_price > 0:
                    p_cost = (calc_distance / mileage) * p_price
                    d_cost = (calc_distance / mileage) * d_price
                    cheaper = "Petrol" if p_cost < d_cost else "Diesel"
                    comparison = {
                        'petrol_cost': p_cost,
                        'diesel_cost': d_cost,
                        'cheaper': cheaper,
                        'difference': abs(p_cost - d_cost)
                    }
            except ValueError:
                pass # Ignore invalid comparison inputs

        # 7. Package results for template
        results = {
            'fuel_required': round(fuel_required, 2),
            'total_cost': total_cost,
            'monthly_cost': monthly_cost,
            'currency': currency,
            'trip_type': trip_type.replace('-', ' ').title(),
            'comparison': comparison
        }

        return render_template('index.html', results=results)

    except ValueError:
        flash("Invalid input. Please enter numerical values.")
        return redirect(url_for('index'))
    except Exception as e:
        # Log error in production environment
        app.logger.error(f"Calculation Error: {str(e)}")
        flash("An internal error occurred. Please try again.")
        return redirect(url_for('index'))

# Production configuration: Debug must be OFF
if __name__ == '__main__':
    app.run(debug=False)
