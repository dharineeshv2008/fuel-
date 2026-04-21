import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, flash, Response

# Load environment variables
load_dotenv()

from utils import (
    calculate_fuel, plan_trip, get_random_tip, format_currency, safe_float
)

# Resolve absolute paths for Vercel serverless compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-fuelwise-super-secret-key")


# --- ERROR HANDLERS ---

@app.errorhandler(404)
def not_found(e):
    return render_template("login.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return "Internal Server Error", 500

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

# --- AUTH ROUTES (DEMO MODE — No Database) ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html")

        # Demo Mode: Accept any credentials
        session["user"] = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": email.split("@")[0].title(),
            "access_token": "demo-token-" + uuid.uuid4().hex[:8]
        }
        session.modified = True
        flash(f"Welcome back, {session['user']['name']}! (Demo Mode)", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        # Demo Mode: Accept any registration
        flash("Account created successfully! Please login. (Demo Mode)", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# --- APP ROUTES (DEMO MODE — In-Memory Data) ---

# In-memory storage for demo session
def _get_demo_store():
    """Get per-session demo data store."""
    if "demo_vehicles" not in session:
        session["demo_vehicles"] = []
    if "demo_trips" not in session:
        session["demo_trips"] = []
    if "demo_fuel_logs" not in session:
        session["demo_fuel_logs"] = []
    return session

@app.route("/")
def dashboard():
    store = _get_demo_store()
    vehicles = store.get("demo_vehicles", [])
    trips = store.get("demo_trips", [])
    fuel_logs = store.get("demo_fuel_logs", [])

    total_spent = sum(float(l.get("total_cost", 0)) for l in fuel_logs)
    total_dist = sum(float(t.get("distance", 0)) for t in trips)
    total_fuel = sum(float(l.get("litres", 0)) for l in fuel_logs)

    recent_activity = []
    for l in fuel_logs[:3]:
        recent_activity.append({"date": l["date"], "text": f"Fuel: {l['litres']}L purchase", "amount": format_currency(l["total_cost"], session.get("currency", "₹")), "icon": "fa-gas-pump"})
    for t in trips[:2]:
        recent_activity.append({"date": t.get("created_at", datetime.now().isoformat()).split("T")[0], "text": f"Trip: {t['distance']}km estimate", "amount": format_currency(t["total_cost"], session.get("currency", "₹")), "icon": "fa-calculator"})

    return render_template("index.html", total_spent=total_spent, total_distance=total_dist, total_fuel=total_fuel, vehicle_count=len(vehicles), recent_activity=recent_activity, tip=get_random_tip(), insight=f"{len(fuel_logs)} fuel logs recorded.")

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    store = _get_demo_store()
    vehicles = store.get("demo_vehicles", [])
    result = None
    form_data = request.form.to_dict() if request.method == "POST" else {}

    if request.method == "POST":
        action = request.form.get("action", "calculate")
        try:
            if action == "save_calc":
                trip = {
                    "id": uuid.uuid4().hex[:12],
                    "distance": safe_float(request.form.get("distance_val")),
                    "total_cost": safe_float(request.form.get("total_cost_val")),
                    "fuel_price": safe_float(request.form.get("price_val")),
                    "vehicle_id": request.form.get("vehicle_id_val") or None,
                    "trip_type": request.form.get("trip_type_val", "one-way"),
                    "passengers": int(safe_float(request.form.get("passengers_val", 1))),
                    "created_at": datetime.now().isoformat()
                }
                session["demo_trips"] = session.get("demo_trips", []) + [trip]
                session.modified = True
                flash("Trip saved to history! (Demo Mode)", "success")
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
                if vehicle_id:
                    result["unit"] = "kWh" if fuel_type == "EV" else "Liters (L)"
                else:
                    result["unit"] = ""
                flash("Calculation complete!", "success")
        except Exception as e: flash(f"Calculator Error: {str(e)}", "error")

    return render_template("calculator.html", vehicles=vehicles, result=result, form=form_data)

@app.route("/vehicles", methods=["GET", "POST"])
def vehicles():
    store = _get_demo_store()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("name", "").strip()
            mileage = safe_float(request.form.get("mileage"))
            tank = safe_float(request.form.get("tank_size"))
            if not name: flash("Vehicle name is required.", "error")
            elif mileage <= 0 or tank <= 0: flash("Mileage and Tank Size must be positive.", "error")
            else:
                vehicle = {
                    "id": uuid.uuid4().hex[:12],
                    "vehicle_name": name,
                    "vehicle_type": request.form.get("type", "car"),
                    "fuel_type": request.form.get("fuel_type", "Petrol"),
                    "mileage": mileage,
                    "tank_size": tank,
                    "year": request.form.get("year", "").strip()
                }
                session["demo_vehicles"] = session.get("demo_vehicles", []) + [vehicle]
                session.modified = True
                flash(f"Vehicle '{name}' added! (Demo Mode)", "success")
                return redirect(url_for("vehicles"))
        elif action == "delete":
            vid = request.form.get("vehicle_id")
            session["demo_vehicles"] = [v for v in session.get("demo_vehicles", []) if v["id"] != vid]
            session.modified = True
            flash("Vehicle removed.", "info")
            return redirect(url_for("vehicles"))

    return render_template("vehicles.html", vehicles=store.get("demo_vehicles", []))

@app.route("/history", methods=["GET", "POST"])
def history():
    store = _get_demo_store()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_log":
            log = {
                "id": uuid.uuid4().hex[:12],
                "date": request.form.get("date"),
                "litres": safe_float(request.form.get("litres")),
                "price": safe_float(request.form.get("price")),
                "total_cost": safe_float(request.form.get("litres")) * safe_float(request.form.get("price")),
                "odometer": safe_float(request.form.get("odometer")),
                "vehicle_id": request.form.get("vehicle") or None,
                "notes": request.form.get("notes", "")
            }
            session["demo_fuel_logs"] = session.get("demo_fuel_logs", []) + [log]
            session.modified = True
            flash("Fuel log saved! (Demo Mode)", "success")
        elif action == "delete_log":
            lid = request.form.get("log_id")
            session["demo_fuel_logs"] = [l for l in session.get("demo_fuel_logs", []) if l["id"] != lid]
            session.modified = True
            flash("Fuel log deleted.", "info")
        elif action == "delete_trip":
            tid = request.form.get("trip_id")
            session["demo_trips"] = [t for t in session.get("demo_trips", []) if t["id"] != tid]
            session.modified = True
            flash("Calculation removed from history.", "info")
        return redirect(url_for("history"))

    vehicles_list = store.get("demo_vehicles", [])
    trips = store.get("demo_trips", [])
    logs = store.get("demo_fuel_logs", [])
    vmap = {v["id"]: v["vehicle_name"] for v in vehicles_list}
    return render_template("history.html", trips=trips, logs=logs, vehicles=vehicles_list, vmap=vmap)

@app.route("/trip", methods=["GET", "POST"])
def trip_planner():
    store = _get_demo_store()
    vehicles = store.get("demo_vehicles", [])
    result = None
    form_data = request.form.to_dict() if request.method == "POST" else {}

    if request.method == "POST":
        try:
            dist = safe_float(request.form.get("total_dist"))
            mileage = safe_float(request.form.get("mileage"))
            price = safe_float(request.form.get("fuel_price"))
            tank = safe_float(request.form.get("tank_size", 45))
            speed = safe_float(request.form.get("speed", 60))

            if dist <= 0 or mileage <= 0 or price <= 0:
                flash("Please provide positive values for Distance, Mileage, and Price.", "error")
            else:
                result = plan_trip(dist, mileage, price, tank, speed)
                flash("Trip planned!", "success")
        except Exception as e:
            flash(f"Trip Planner Error: {str(e)}", "error")

    return render_template("trip.html", vehicles=vehicles, result=result, form=form_data)

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
