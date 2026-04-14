import random
import os
import bcrypt
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

# --- TASK 1: SUPABASE CLIENT SETUP & DEBUG ---
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

print(f"DEBUG: SUPABASE_URL: {url[:15]}...") # Masked for security
if not url or not key:
    print("CRITICAL ERROR: SUPABASE_URL or SUPABASE_KEY missing from environment!")

supabase: Client = create_client(url, key)

# --- UTILITIES ---

def safe_float(value, default=0.0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- CORE CALCULATIONS ---

def get_efficiency_rating(mileage, fuel_type="Petrol"):
    if fuel_type == "EV":
        if mileage >= 7: return "Super Efficient 🍃"
        if mileage >= 5: return "Great Efficiency ✨"
        if mileage >= 3: return "Average Economy 🚗"
        return "Heavy Consumer 🔋"
    else:
        if mileage >= 25: return "Super Efficient 🍃"
        if mileage >= 18: return "Great Mileage ✨"
        if mileage >= 12: return "Average Economy 🚗"
        return "Heavy Consumer ⛽"

def calculate_fuel(distance, mileage, fuel_price, trip_type, passengers, daily_km, fuel_type="Petrol"):
    passengers = max(1, passengers)
    actual_distance = distance * 2 if trip_type == "round-trip" else distance
    fuel_needed = actual_distance / mileage
    total_cost = fuel_needed * fuel_price
    cost_per_km = total_cost / actual_distance
    cost_per_passenger = total_cost / passengers
    
    co2_factors = {"Petrol": 2.31, "Diesel": 2.68, "CNG": 2.0, "EV": 0.0}
    co2_emissions = fuel_needed * co2_factors.get(fuel_type, 2.31)
    consumption = (fuel_needed / actual_distance) * 100 
    
    wear_tear = actual_distance * 0.15
    total_trip_impact = total_cost + wear_tear
    
    savings_potential = 0
    if mileage < 20: 
        optimal_fuel = actual_distance / 20
        savings_potential = (fuel_needed - optimal_fuel) * fuel_price

    monthly_cost = (daily_km * 30 / mileage) * fuel_price if daily_km > 0 else 0
    yearly_cost = (daily_km * 365 / mileage) * fuel_price if daily_km > 0 else 0
        
    return {
        "distance": actual_distance, "fuel_needed": fuel_needed, "total_cost": total_cost,
        "cost_per_km": cost_per_km, "cost_per_passenger": cost_per_passenger,
        "rating": get_efficiency_rating(mileage, fuel_type), "co2": co2_emissions,
        "consumption": consumption, "monthly_cost": monthly_cost, "yearly_cost": yearly_cost,
        "wear_tear": wear_tear, "total_impact": total_trip_impact, "savings_potential": savings_potential
    }

def plan_trip(total_dist, mileage, fuel_price, tank_size, speed):
    tank_size = max(1, tank_size)
    speed = max(1, speed)
    total_fuel = total_dist / mileage
    total_cost = total_fuel * fuel_price
    travel_time = total_dist / speed
    range_per_tank = tank_size * mileage
    num_stops = max(0, int((total_dist - 0.1) // range_per_tank))
    
    stops = []
    for i in range(1, num_stops + 1):
        stop_km = min(range_per_tank * i, total_dist)
        stops.append({"num": i, "km": round(stop_km, 1), "litres": round(tank_size, 1), "cost": round(tank_size * fuel_price, 2)})
            
    return {"total_dist": total_dist, "total_fuel": total_fuel, "total_cost": total_cost, "travel_time": travel_time, "range": range_per_tank, "num_stops": num_stops, "stops": stops}

def get_random_tip():
    tips = ["Maintain steady speeds.", "Keep tires properly inflated.", "Avoid carrying unnecessary weight.", "Use cruise control on highways.", "Plan trips during off-peak hours.", "Service your engine regularly.", "Avoid excessive idling.", "Use recommended motor oil.", "Close windows at highway speeds.", "Combine multiple errands.", "Shift to higher gears smoothly.", "Air conditioning can increase consumption.", "Park in the shade.", "Slow down.", "Remove roof racks when not in use."]
    return random.choice(tips)

def format_currency(amount, symbol):
    return f"{symbol}{float(amount or 0):,.2f}"

# --- DATABASE HELPERS ---

def db_insert_user(user_id, name, email, password):
    """Insert user into public table with explicit print logs."""
    try:
        print(f"DEBUG: Attempting to insert profile for user_id: {user_id}")
        # Task 2: Use explicit .insert() as requested
        res = supabase.table("users").insert({
            "id": user_id,
            "name": name,
            "email": email,
            "password": hash_password(password)
        }).execute()
        print(f"DEBUG: Supabase Profile Insert Response: {res}")
        return res
    except Exception as e:
        print(f"CRITICAL: Failed to insert profile for user {email}: {str(e)}")
        raise e

def db_get_vehicles(user_id):
    return supabase.table("vehicles").select("*").eq("user_id", user_id).execute()

def db_insert_vehicle(user_id, data):
    data["user_id"] = user_id
    return supabase.table("vehicles").insert(data).execute()

def db_delete_vehicle(user_id, vehicle_id):
    return supabase.table("vehicles").delete().eq("user_id", user_id).eq("id", vehicle_id).execute()

def db_get_trips(user_id):
    return supabase.table("trips").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()

def db_insert_trip(user_id, data):
    data["user_id"] = user_id
    return supabase.table("trips").insert(data).execute()

def db_delete_trip(user_id, trip_id):
    return supabase.table("trips").delete().eq("user_id", user_id).eq("id", trip_id).execute()

def db_get_fuel_logs(user_id):
    return supabase.table("fuel_logs").select("*").eq("user_id", user_id).order("date", desc=True).execute()

def db_insert_fuel_log(user_id, data):
    data["user_id"] = user_id
    if "total_cost" not in data and "litres" in data and "price" in data:
        data["total_cost"] = float(data["litres"]) * float(data["price"])
    return supabase.table("fuel_logs").insert(data).execute()

def db_delete_fuel_log(user_id, log_id):
    return supabase.table("fuel_logs").delete().eq("user_id", user_id).eq("id", log_id).execute()
