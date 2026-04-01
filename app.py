import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

import uuid
import csv
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, Response
from utils import calculate_fuel, plan_trip, get_random_tip, format_currency, get_monthly_insight

# Explicitly set paths for Vercel deployment safety
base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, "templates"), static_folder=os.path.join(base_dir, "static"))
# Secret key for session management
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-fuelwise-super-secret-key")

# Helper to ensure defaults exist in session
def ensure_session_defaults():
    if "theme" not in session:
        session["theme"] = "light"
    if "currency" not in session:
        session["currency"] = "₹"
    if "default_price" not in session:
        session["default_price"] = ""
    if "unit" not in session:
        session["unit"] = "km"
        
    if "vehicles" not in session:
        session["vehicles"] = []
    else:
        # Migration: Ensure all vehicles have new required keys
        modified = False
        for v in session["vehicles"]:
            if "vehicleType" not in v:
                v["vehicleType"] = v.pop("type", "car")
                modified = True
            if "fuelType" not in v:
                v["fuelType"] = "Petrol"
                modified = True
            if "batteryRange" not in v:
                v["batteryRange"] = v.get("tankSize", 0) if v["fuelType"] == "EV" else 0
                modified = True
            if "id" not in v:
                v["id"] = str(uuid.uuid4())
                modified = True
        if modified:
            session.modified = True

    if "fuel_logs" not in session:
        session["fuel_logs"] = []
    if "calc_history" not in session:
        session["calc_history"] = []
    else:
        # Migration: Ensure all history entries have a unit
        modified = False
        for c in session["calc_history"]:
            if "unit" not in c:
                c["unit"] = "L"
                modified = True
        if modified:
            session.modified = True
            
    if "trips" not in session:
        session["trips"] = []
        
    if "user" not in session:
        session["user"] = None # Stores {email, name} when logged in

@app.before_request
def before_request():
    ensure_session_defaults()
    
    # Simple route protection: redirect to login if not logged in and not on auth pages
    auth_routes = ["login", "register", "static"]
    if not session.get("user") and request.endpoint not in auth_routes and request.endpoint:
        return redirect(url_for("login"))

# Context processors to make data available to all templates
@app.context_processor
def inject_globals():
    return {
        "theme": session.get("theme", "light"),
        "currency": session.get("currency", "₹"),
        "format_currency": lambda x: format_currency(x, session.get("currency", "₹")),
        "now": datetime.now(),
        "user": session.get("user")
    }

# ----------------------------------------------------
# AUTH ROUTES
# ----------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # As requested: "accept any email format and password"
        if email and password:
            session["user"] = {"email": email, "name": email.split("@")[0].capitalize()}
            session.modified = True
            flash(f"Welcome back, {session['user']['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Please enter both email and password.", "error")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if name and email and password:
            session["user"] = {"email": email, "name": name}
            session.modified = True
            flash(f"Account created successfully! Welcome, {name}.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("All fields are required.", "error")
            
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.modified = True
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ----------------------------------------------------
# PAGE ROUTES
# ----------------------------------------------------

@app.route("/")
def dashboard():
    total_spent = sum(log["total_cost"] for log in session["fuel_logs"])
    total_fuel = sum(log["litres"] for log in session["fuel_logs"])
    total_distance = sum(c["distance"] for c in session["calc_history"])
    vehicle_count = len(session["vehicles"])
    
    # Recent activity = mix of latest fuel logs and calcs
    recent_activity = []
    for log in session["fuel_logs"][:5]:
        recent_activity.append({
            "type": "log",
            "date": log["date"],
            "text": f"{log['litres']:.1f}L fuel @ {format_currency(log['price'], session['currency'])}/L",
            "amount": format_currency(log['total_cost'], session['currency']),
            "icon": "fa-gas-pump"
        })
    for calc in session["calc_history"][:3]:
        recent_activity.append({
            "type": "calc",
            "date": calc["date"],
            "text": f"{calc['distance']} km trip calculated",
            "amount": format_currency(calc['total_cost'], session['currency']),
            "icon": "fa-calculator"
        })
        
    recent_activity.sort(key=lambda x: x["date"], reverse=True)
    recent_activity = recent_activity[:5]
    
    return render_template("index.html",
                           total_spent=total_spent,
                           total_fuel=total_fuel,
                           total_distance=total_distance,
                           vehicle_count=vehicle_count,
                           recent_activity=recent_activity,
                           tip=get_random_tip(),
                           insight=get_monthly_insight(session["fuel_logs"]))

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    result = None
    if request.method == "POST":
        try:
            # Handle action (calculate or save)
            action = request.form.get("action", "calculate")
            
            if action == "save_calc":
                # User clicked "Save to history"
                calc_data = {
                    "id": str(uuid.uuid4()),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "distance": float(request.form.get("distance_val", 0)),
                    "fuel_needed": float(request.form.get("fuel_needed_val", 0)),
                    "total_cost": float(request.form.get("total_cost_val", 0)),
                    "trip_type": request.form.get("trip_type_val", ""),
                    "unit": request.form.get("unit_val", "L")
                }
                session["calc_history"].insert(0, calc_data)
                session.modified = True
                flash("Calculation saved to history!", "success")
                return redirect(url_for("calculator"))
                
            elif action == "export_calc":
                # Create CSV on the fly
                rows = [
                    ["Metric", "Value"],
                    ["Distance (km)", request.form.get("distance_val")],
                    ["Fuel Needed (L)", request.form.get("fuel_needed_val")],
                    ["Total Cost", request.form.get("total_cost_val")],
                    ["Cost per km", request.form.get("cost_km_val")],
                    ["Cost per Passenger", request.form.get("cost_pass_val")]
                ]
                def generate():
                    for r in rows:
                        yield f'{r[0]},{r[1]}\n'
                return Response(generate(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=fuel_calculation.csv"})

            # Handle normal calculation
            dist_str = request.form.get("distance") or "0"
            mileage_str = request.form.get("mileage") or "0"
            price_str = request.form.get("fuel_price") or "0"
            dist = float(dist_str)
            price = float(price_str)
            
            # Fetch from vehicle if mileage is empty
            vehicle_id = request.form.get("vehicle_id")
            effective_mileage = float(mileage_str)
            fuel_type = "Petrol"
            
            if vehicle_id:
                for v in session["vehicles"]:
                    if v["id"] == vehicle_id:
                        fuel_type = v.get("fuelType", "Petrol")
                        if effective_mileage <= 0:
                            effective_mileage = v["mileage"]
                        break
            
            trip_type = request.form.get("trip_type", "one-way")
            passengers = float(request.form.get("passengers") or 1)
            daily_km = float(request.form.get("daily_km") or 0)
            budget = float(request.form.get("budget") or 0)
            
            # Form data for persistence
            form_data = request.form.to_dict()
            if not form_data.get("mileage") and effective_mileage > 0:
                form_data["mileage"] = str(effective_mileage)

            if action == "refresh":
                # Skip calculation validation, just update the form with mileage
                return render_template("calculator.html", vehicles=session["vehicles"], form=form_data)

            if dist <= 0 or effective_mileage <= 0 or price <= 0:
                raise ValueError("Distance, Mileage, and Fuel Price must be greater than zero.")
            
            result = calculate_fuel(dist, effective_mileage, price, trip_type, passengers, daily_km, fuel_type)
            result["budget"] = budget
            
            flash("Calculation complete!", "success")
            return render_template("calculator.html", vehicles=session["vehicles"], result=result, form=form_data)
        except ValueError as e:
            flash(str(e), "error")
            # Preserve the processed form_data (with filled-in mileage) on error
            return render_template("calculator.html", vehicles=session["vehicles"], form=form_data if 'form_data' in locals() else request.form.to_dict())

    return render_template("calculator.html", vehicles=session["vehicles"], form={"fuel_price": session["default_price"]})

@app.route("/trip", methods=["GET", "POST"])
def trip_planner():
    result = None
    if request.method == "POST":
        try:
            dist_str = request.form.get("total_dist") or "0"
            mileage_str = request.form.get("mileage") or "0"
            price_str = request.form.get("fuel_price") or "0"
            
            dist = float(dist_str)
            price = float(price_str)
            
            # Fetch from vehicle if mileage is empty
            vehicle_id = request.form.get("vehicle_id")
            effective_mileage = float(mileage_str)
            
            if effective_mileage <= 0 and vehicle_id:
                for v in session["vehicles"]:
                    if v["id"] == vehicle_id:
                        effective_mileage = v["mileage"]
                        break
            
            tank = float(request.form.get("tank_size") or 45)
            speed = float(request.form.get("speed") or 60)
            
            if dist <= 0 or effective_mileage <= 0 or price <= 0:
                raise ValueError("Distance, Mileage, and Fuel Price must be greater than zero.")
            
            result = plan_trip(dist, effective_mileage, price, tank, speed)
            flash("Trip planned successfully!", "success")
            return render_template("trip.html", vehicles=session["vehicles"], result=result, form=request.form.to_dict())
            
        except ValueError as e:
            flash(str(e), "error")
            return render_template("trip.html", vehicles=session["vehicles"], form=request.form.to_dict())

    return render_template("trip.html", vehicles=session["vehicles"], form={"fuel_price": session["default_price"]})

@app.route("/vehicles", methods=["GET", "POST"])
def vehicles():
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add":
            fuel_type = request.form.get("fuelType", "Petrol")
            mileage = float(request.form.get("mileage", 0) or 0)
            tank_size = float(request.form.get("tankSize", 0) or 0)
            name = request.form.get("name", "").strip()
            
            # Validation logic based on fuel type
            is_valid = True
            error_msg = ""
            
            if not name:
                is_valid = False
                error_msg = "Vehicle name is required."
            elif fuel_type in ["Petrol", "Diesel"]:
                if mileage <= 0:
                    is_valid = False
                    error_msg = "Mileage must be greater than 0 for Petrol/Diesel vehicles."
                elif tank_size <= 0:
                    is_valid = False
                    error_msg = "Tank size must be greater than 0 for Petrol/Diesel vehicles."
            elif fuel_type == "EV":
                if mileage <= 0:
                    is_valid = False
                    error_msg = "Efficiency (km/kWh) must be greater than 0 for EV."
                # tankSize (Battery) is optional for EV
            elif fuel_type == "CNG":
                if mileage <= 0:
                    is_valid = False
                    error_msg = "Mileage must be greater than 0 for CNG vehicles."
                # tankSize is optional for CNG
            
            if not is_valid:
                flash(error_msg, "error")
                return render_template("vehicles.html", vehicles=session["vehicles"])
            else:
                v = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "vehicleType": request.form.get("type", "car"),
                    "mileage": mileage,
                    "fuelType": fuel_type,
                    "tankSize": tank_size if fuel_type != "EV" else 0,
                    "batteryRange": tank_size if fuel_type == "EV" else 0,
                    "year": request.form.get("year", "").strip()
                }
                session["vehicles"].append(v)
                session.modified = True
                flash(f"Vehicle '{v['name']}' added!", "success")
                
        elif action == "delete":
            vid = request.form.get("vehicle_id")
            session["vehicles"] = [v for v in session["vehicles"] if v["id"] != vid]
            session.modified = True
            flash("Vehicle removed.", "info")
            
        if action in ["refresh", "add"]:
            return render_template("vehicles.html", vehicles=session["vehicles"])
        return redirect(url_for("vehicles"))
        
    return render_template("vehicles.html", vehicles=session["vehicles"])

@app.route("/history", methods=["GET", "POST"])
def history():
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add_log":
            try:
                litres = float(request.form.get("litres", 0))
                price = float(request.form.get("price", 0))
                if litres <= 0 or price <= 0:
                    raise ValueError("Enter valid litres and price.")
                    
                log = {
                    "id": str(uuid.uuid4()),
                    "date": request.form.get("date"),
                    "litres": litres,
                    "price": price,
                    "total_cost": litres * price,
                    "odometer": float(request.form.get("odometer", 0) or 0),
                    "vehicleId": request.form.get("vehicle", ""),
                    "notes": request.form.get("notes", "").strip()
                }
                session["fuel_logs"].insert(0, log)
                session.modified = True
                flash("Fuel log added!", "success")
            except ValueError as e:
                flash(str(e), "error")
                
        elif action == "delete_log":
            lid = request.form.get("log_id")
            session["fuel_logs"] = [l for l in session["fuel_logs"] if l["id"] != lid]
            session.modified = True
            flash("Log entry removed.", "info")
            
        elif action == "delete_calc":
            cid = request.form.get("calc_id")
            session["calc_history"] = [c for c in session["calc_history"] if c["id"] != cid]
            session.modified = True
            flash("Calculation removed.", "info")
            
        return redirect(url_for("history"))

    logs = session["fuel_logs"]
    # Provide vehicle map for display
    vmap = {v["id"]: v["name"] for v in session["vehicles"]}
    
    return render_template("history.html", logs=logs, calcs=session["calc_history"], vehicles=session["vehicles"], vmap=vmap)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        action = request.form.get("action", "save")
        
        if action == "save":
            session["theme"] = request.form.get("theme", "light")
            session["currency"] = request.form.get("currency", "₹")
            session["default_price"] = request.form.get("default_price", "")
            session["unit"] = request.form.get("unit", "km")
            session.modified = True
            flash("Settings saved!", "success")
            
        elif action == "reset":
            session.clear()
            ensure_session_defaults()
            flash("All data has been reset.", "info")
            return redirect(url_for("dashboard"))
            
        return redirect(url_for("settings"))
        
    return render_template("settings.html")

# Auto-run
if __name__ == "__main__":
    print("🚗 Fuel Cost Calculator running at http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
