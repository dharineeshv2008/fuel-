import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, Response

# Load environment variables
load_dotenv()

from utils import (
    calculate_fuel, plan_trip, get_random_tip, format_currency,
    supabase, db_insert_user, db_get_vehicles,
    db_insert_vehicle, db_delete_vehicle, db_get_trips, db_insert_trip,
    db_delete_trip, db_get_fuel_logs, db_insert_fuel_log, db_delete_fuel_log,
    safe_float
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-fuelwise-super-secret-key")

# --- MIDDLEWARE & GLOBALS ---

@app.before_request
def auth_middleware():
    """Ensure user is logged in for protected routes."""
    public_endpoints = ["login", "register", "static"]
    if not session.get("user") and request.endpoint not in public_endpoints and request.endpoint:
        return redirect(url_for("login"))

@app.context_processor
def inject_globals():
    """Global data for templates."""
    currency = session.get("currency", "₹")
    return {
        "theme": session.get("theme", "light"),
        "currency": currency,
        "format_currency": lambda x: format_currency(x, currency),
        "now": datetime.now(),
        "user": session.get("user")
    }

# --- AUTH ROUTES ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        print(f"DEBUG: Login Attempt - Email: {email}") # Log login attempt
        
        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                session["user"] = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": response.user.user_metadata.get("name", email.split("@")[0]),
                    "access_token": response.session.access_token
                }
                session.modified = True
                print(f"DEBUG: Login Successful for: {email}")
                flash(f"Welcome back, {session['user']['name']}!", "success")
                return redirect(url_for("dashboard"))
        except Exception as e:
            print(f"DEBUG: Login Failed: {str(e)}")
            flash("Invalid email or password.", "error")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        # Task 2: Correct Form Reading & Debug Prints
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        print(f"DEBUG: Registration Form Data Received:")
        print(f"  - Name: {name}")
        print(f"  - Email: {email}")
        print(f"  - Password Len: {len(password) if password else 0}")
        
        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        try:
            # Task 2: Supabase Auth Signup
            print(f"DEBUG: Attempting Supabase Auth sign_up for {email}...")
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": {"name": name}}
            })
            print(f"DEBUG: Supabase Auth Response: {response}")
            
            if response.user:
                print(f"DEBUG: Auth Successful. Syncing to public.users for user_id {response.user.id}")
                # Task 2: Sync to public.users table
                db_insert_user(response.user.id, name, email, password)
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("login"))
            else:
                print("DEBUG: Registration failed: No user returned in response.")
                flash("Signup failed. Please try again.", "error")
                
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG: Registration ERROR: {error_msg}")
            if "already registered" in error_msg.lower():
                flash("Email already in use.", "error")
            else:
                flash(f"Registration failed: {error_msg}", "error")
            
    return render_template("register.html")

@app.route("/logout")
def logout():
    try: supabase.auth.sign_out()
    except: pass
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# --- APP ROUTES ---

@app.route("/")
def dashboard():
    user_id = session["user"]["id"]
    try:
        vehicles = db_get_vehicles(user_id).data
        trips = db_get_trips(user_id).data
        fuel_logs = db_get_fuel_logs(user_id).data
        
        total_spent = sum(float(l.get("total_cost", 0)) for l in fuel_logs)
        total_dist = sum(float(t.get("distance", 0)) for t in trips)
        
        recent_activity = []
        for l in fuel_logs[:3]:
            recent_activity.append({"date": l["date"], "text": f"Fuel: {l['litres']}L purchase", "amount": format_currency(l["total_cost"], session.get("currency", "₹")), "icon": "fa-gas-pump"})
        for t in trips[:2]:
            recent_activity.append({"date": t["created_at"].split("T")[0], "text": f"Trip: {t['distance']}km estimate", "amount": format_currency(t["total_cost"], session.get("currency", "₹")), "icon": "fa-calculator"})
            
        return render_template("index.html", total_spent=total_spent, total_distance=total_dist, vehicle_count=len(vehicles), recent_activity=recent_activity, tip=get_random_tip(), insight=f"{len(fuel_logs)} fuel logs recorded.")
    except Exception as e:
        flash(f"Dashboard Error: {str(e)}", "error")
        return render_template("index.html", total_spent=0, total_distance=0, vehicle_count=0, recent_activity=[], tip=get_random_tip())

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    user_id = session["user"]["id"]
    vehicles = db_get_vehicles(user_id).data
    result = None
    form_data = request.form.to_dict() if request.method == "POST" else {}
    
    if request.method == "POST":
        action = request.form.get("action", "calculate")
        try:
            if action == "save_calc":
                db_insert_trip(user_id, {"distance": safe_float(request.form.get("distance_val")), "total_cost": safe_float(request.form.get("total_cost_val")), "fuel_price": safe_float(request.form.get("price_val")), "vehicle_id": request.form.get("vehicle_id_val") or None, "trip_type": request.form.get("trip_type_val", "one-way"), "passengers": int(safe_float(request.form.get("passengers_val", 1)))})
                flash("Trip saved to history!", "success")
                return redirect(url_for("calculator"))

            dist = safe_float(request.form.get("distance"))
            mileage = safe_float(request.form.get("mileage"))
            price = safe_float(request.form.get("fuel_price"))
            
            vehicle_id = request.form.get("vehicle_id")
            fuel_type = "Petrol"
            if vehicle_id:
                for v in vehicles:
                    if v["id"] == vehicle_id:
                        fuel_type = v.get("fuel_type", "Petrol")
                        if mileage <= 0: mileage = safe_float(v.get("mileage"))
                        break

            if action == "refresh":
                form_data["mileage"] = str(mileage) if mileage > 0 else ""
                return render_template("calculator.html", vehicles=vehicles, form=form_data)

            if dist <= 0 or mileage <= 0 or price <= 0:
                flash("Please provide positive values for Distance, Mileage, and Price.", "error")
            else:
                result = calculate_fuel(dist, mileage, price, request.form.get("trip_type", "one-way"), int(safe_float(request.form.get("passengers", 1))), safe_float(request.form.get("daily_km")), fuel_type)
                result["fuel_price"] = price
                flash("Calculation complete!", "success")
        except Exception as e: flash(f"Calculator Error: {str(e)}", "error")

    return render_template("calculator.html", vehicles=vehicles, result=result, form=form_data)

@app.route("/vehicles", methods=["GET", "POST"])
def vehicles():
    user_id = session["user"]["id"]
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("name", "").strip()
            mileage = safe_float(request.form.get("mileage"))
            tank = safe_float(request.form.get("tank_size"))
            if not name: flash("Vehicle name is required.", "error")
            elif mileage <= 0 or tank <= 0: flash("Mileage and Tank Size must be positive.", "error")
            else:
                try:
                    db_insert_vehicle(user_id, {"vehicle_name": name, "vehicle_type": request.form.get("type", "car"), "fuel_type": request.form.get("fuel_type", "Petrol"), "mileage": mileage, "tank_size": tank, "year": request.form.get("year", "").strip()})
                    flash(f"Vehicle '{name}' added!", "success")
                except Exception as e: flash(f"Database Error: {str(e)}", "error")
                return redirect(url_for("vehicles"))
        elif action == "delete":
            db_delete_vehicle(user_id, request.form.get("vehicle_id"))
            flash("Vehicle removed.", "info")
            return redirect(url_for("vehicles"))
            
    try: 
        vehicles_list = db_get_vehicles(user_id).data
        return render_template("vehicles.html", vehicles=vehicles_list)
    except: return render_template("vehicles.html", vehicles=[])

@app.route("/history", methods=["GET", "POST"])
def history():
    user_id = session["user"]["id"]
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "add_log":
                db_insert_fuel_log(user_id, {"date": request.form.get("date"), "litres": safe_float(request.form.get("litres")), "price": safe_float(request.form.get("price")), "odometer": safe_float(request.form.get("odometer")), "vehicle_id": request.form.get("vehicle") or None, "notes": request.form.get("notes", "")})
                flash("Fuel log saved!", "success")
            elif action == "delete_log":
                db_delete_fuel_log(user_id, request.form.get("log_id"))
                flash("Fuel log deleted.", "info")
            elif action == "delete_trip":
                db_delete_trip(user_id, request.form.get("trip_id"))
                flash("Calculation removed from history.", "info")
        except Exception as e: flash(f"Action failed: {str(e)}", "error")
        return redirect(url_for("history"))

    try:
        vehicles = db_get_vehicles(user_id).data
        trips = db_get_trips(user_id).data
        logs = db_get_fuel_logs(user_id).data
        vmap = {v["id"]: v["vehicle_name"] for v in vehicles}
        return render_template("history.html", trips=trips, logs=logs, vehicles=vehicles, vmap=vmap)
    except: return render_template("history.html", trips=[], logs=[], vehicles=[], vmap={})

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        session["currency"] = request.form.get("currency", "₹")
        session["theme"] = request.form.get("theme", "light")
        session.modified = True
        flash("Settings updated!", "success")
        return redirect(url_for("dashboard"))
    return render_template("settings.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
