import random

# Core Calculation Logic

def get_efficiency_rating(mileage):
    """Return an efficiency rating string based on km/L."""
    if mileage >= 25:
        return "Super Efficient 🍃"
    if mileage >= 18:
        return "Great Mileage ✨"
    if mileage >= 12:
        return "Average Economy 🚗"
    return "Heavy Consumer ⛽"

def calculate_fuel(distance, mileage, fuel_price, trip_type, passengers, daily_km):
    """
    Calculate essential fuel metrics and budget projections.
    Returns a dictionary of calculated metrics.
    """
    # Validation checks
    if distance <= 0 or mileage <= 0 or fuel_price <= 0:
        raise ValueError("Distance, Mileage, and Fuel Price must be greater than zero.")
    
    passengers = max(1, passengers)
    
    actual_distance = distance * 2 if trip_type == "round-trip" else distance
    fuel_needed = actual_distance / mileage
    total_cost = fuel_needed * fuel_price
    cost_per_km = total_cost / actual_distance
    cost_per_passenger = total_cost / passengers
    
    # 2.31 kg of CO2 per litre of petrol/diesel (avg)
    co2_emissions = fuel_needed * 2.31
    consumption = (fuel_needed / actual_distance) * 100 # L/100km
    
    # Monthly/Yearly projections
    monthly_cost = 0
    yearly_cost = 0
    if daily_km > 0:
        monthly_cost = (daily_km * 30 / mileage) * fuel_price
        yearly_cost = (daily_km * 365 / mileage) * fuel_price
        
    return {
        "distance": actual_distance,
        "fuel_needed": fuel_needed,
        "total_cost": total_cost,
        "cost_per_km": cost_per_km,
        "cost_per_passenger": cost_per_passenger,
        "rating": get_efficiency_rating(mileage),
        "co2": co2_emissions,
        "consumption": consumption,
        "monthly_cost": monthly_cost,
        "yearly_cost": yearly_cost
    }

def plan_trip(total_dist, mileage, fuel_price, tank_size, speed):
    """
    Plan a long-distance trip with fuel stops.
    Returns a dictionary of trip metrics and a list of fuel stops.
    """
    if total_dist <= 0 or mileage <= 0 or fuel_price <= 0:
        raise ValueError("Distance, Mileage, and Fuel Price must be greater than zero.")
        
    tank_size = max(1, tank_size)
    speed = max(1, speed)
    
    total_fuel = total_dist / mileage
    total_cost = total_fuel * fuel_price
    travel_time = total_dist / speed
    
    range_per_tank = tank_size * mileage
    num_stops = max(0, int((total_dist - 0.1) // range_per_tank))
    
    stops = []
    if num_stops > 0:
        for i in range(1, num_stops + 1):
            stop_km = min(range_per_tank * i, total_dist)
            fuel_at_stop = tank_size
            cost_at_stop = fuel_at_stop * fuel_price
            
            stops.append({
                "num": i,
                "km": round(stop_km, 1),
                "litres": round(fuel_at_stop, 1),
                "cost": round(cost_at_stop, 2)
            })
            
    return {
        "total_dist": total_dist,
        "total_fuel": total_fuel,
        "total_cost": total_cost,
        "travel_time": travel_time,
        "range": range_per_tank,
        "num_stops": num_stops,
        "stops": stops
    }

def get_random_tip():
    """Return a random fuel saving tip."""
    tips = [
        "Maintain steady speeds — aggressive driving can reduce efficiency by up to 33%.",
        "Keep tires properly inflated. Under-inflated tires increase fuel consumption by 3%.",
        "Avoid carrying unnecessary weight. Every 45 kg reduces efficiency by about 2%.",
        "Use cruise control on highways for consistent fuel usage.",
        "Plan trips during off-peak hours to avoid stop-and-go traffic.",
        "Service your engine regularly for optimal fuel efficiency.",
        "Avoid excessive idling — turn off your engine if waiting more than 60 seconds.",
        "Use the recommended grade of motor oil to improve efficiency by 1-2%.",
        "Close windows at highway speeds to reduce aerodynamic drag.",
        "Combine multiple errands into one trip to reduce total distance.",
        "Shift to higher gears smoothly and as early as possible.",
        "Air conditioning can increase fuel consumption by up to 10%.",
        "Park in the shade to reduce fuel evaporation and keep the cabin cool.",
        "Slow down — driving at 100 km/h vs 120 km/h can save up to 20% fuel.",
        "Remove roof racks/boxes when not in use to reduce drag."
    ]
    return random.choice(tips)

def format_currency(amount, symbol):
    """Format an amount as currency."""
    return f"{symbol}{float(amount):,.2f}"

def format_hours(hours_float):
    """Format decimal hours into 'X_h Y_m'."""
    hrs = int(hours_float)
    mins = round((hours_float - hrs) * 60)
    return f"{hrs}h {mins}m"
