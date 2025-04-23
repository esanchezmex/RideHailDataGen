import threading
import time
import random
import math
import numpy as np
import json
import io
import fastavro
from openai import OpenAI
import os
from azure.eventhub import EventHubProducerClient, EventData

openai_api_key = os.environ.get("OPENAI_API_KEY")
if openai_api_key is None:
    raise ValueError("Missing OpenAI API key. Set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=openai_api_key)

# EventHub configuration
CONNECTION_STRING = os.environ.get("EVENTHUB_CONNECTION_STRING")
PASSENGER_EVENTHUB_NAME = os.environ.get("passengers_eventhub_name", "passenger-requests")
DRIVER_EVENTHUB_NAME = os.environ.get("drivers_eventhub_name", "driver-updates")


def generate_system_message(passenger_id: str) -> str:

    prompt = (
        f"Generate a short message (max 20 words) simulating a text from a uber passenger to the driver"
    )
    try:
        response = client.chat.completions.create(model="gpt-4o-mini",  
        messages=[
            {"role": "system", "content": "You are a helpful ride-hailing system."},
            {"role": "user", "content": prompt}
        ])
        ai_message = response.choices[0].message.content.strip()
        return ai_message
    except Exception as e:
        print("Error generating AI message:", e)
        return "Welcome to our service! We hope you enjoy your ride."


# AVRO Schemas
PASSENGER_REQUEST_SCHEMA = {
    "type": "record",
    "name": "PassengerRequest",
    "namespace": "com.example.ridehailing",
    "fields": [
        {"name": "request_id", "type": "string", "doc": "Unique ID for this request"},
        {"name": "passenger_id", "type": "string", "doc": "Unique identifier of the passenger"},
        {"name": "timestamp", "type": "long", "doc": "Epoch time (milliseconds) when the request was created"},
        {"name": "pickup_location", "type": {
            "type": "record",
            "name": "Location",
            "fields": [
                {"name": "latitude", "type": "double"},
                {"name": "longitude", "type": "double"}
            ]
        }, "doc": "Nested record to store pickup latitude, longitude, and optional address"},
        {"name": "dropoff_location", "type": "Location", "doc": "Reusing the same 'Location' record for dropoff details"},
        {"name": "vehicle_type", "type": {
            "type": "enum",
            "name": "VehicleType",
            "symbols": ["ECONOMY", "STANDARD", "LUXURY", "POOL", "SUV", "ELECTRIC"]
        }, "doc": "Enum for various ride options"},
        {"name": "passenger_preferences", "type": {
            "type": "record",
            "name": "PassengerPreferences",
            "fields": [
                {"name": "music", "type": {
                    "type": "enum",
                    "name": "MusicPreference",
                    "symbols": ["NO_PREFERENCE", "POP", "ROCK", "CLASSICAL", "JAZZ", "HIP_HOP"]
                }, "default": "NO_PREFERENCE"},
                {"name": "temperature", "type": "int", "default": 22, "doc": "Desired in-car temperature in Celsius"},
                {"name": "quiet_ride", "type": "boolean", "default": False, "doc": "Passenger wants minimal conversation"}
            ]
        }, "doc": "Nested record for passenger preferences"},
        {"name": "payment_info", "type": {
            "type": "record",
            "name": "PaymentInfo",
            "fields": [
                {"name": "payment_method", "type": {
                    "type": "enum",
                    "name": "PaymentMethod",
                    "symbols": ["CASH", "CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "APPLE_PAY", "GOOGLE_PAY"]
                }},
                {"name": "coupon_codes", "type": {"type": "array", "items": "string"}, "default": [], "doc": "Any coupon codes the passenger applied"},
                {"name": "loyalty_points_used", "type": ["null", "int"], "default": None, "doc": "Points redeemed from a loyalty program"}
            ]
        }, "doc": "Payment details including method and any discounts/loyalty usage"},
        {"name": "estimated_fare", "type": "float", "doc": "Estimated fare in the local currency"},
        {"name": "text_messages", "type": {
            "type": "array",
            "items": {
                "type": "record",
                "name": "TextMessage",
                "fields": [
                    {"name": "message_id", "type": "string", "doc": "Unique ID for each message"},
                    {"name": "sender", "type": {
                        "type": "enum",
                        "name": "SenderType",
                        "symbols": ["DRIVER", "PASSENGER", "SYSTEM"]
                    }, "doc": "Who sent the message"},
                    {"name": "content", "type": "string", "doc": "Text content of the message"},
                    {"name": "sent_at", "type": "long", "doc": "Epoch time (milliseconds) when the message was sent"}
                ]
            }
        }, "default": [], "doc": "List of text messages exchanged between driver and passenger"},
        {"name": "driver_rating", "type": ["null", "float"], "default": None, "doc": "Optional rating that passenger gave on a previous ride (for predictive analytics)"}
    ]
}

DRIVER_UPDATE_SCHEMA = {
    "type": "record",
    "name": "DriverAvailabilityUpdate",
    "namespace": "com.yourcompany.ridehailing",
    "doc": "Event representing a driver's availability/status update.",
    "fields": [
        {"name": "driver_id", "type": "string", "doc": "Unique identifier for the driver."},
        {"name": "timestamp", "type": "long", "doc": "Epoch timestamp in milliseconds indicating when the update occurred."},
        {"name": "latitude", "type": "double", "doc": "Driver's last known GPS latitude."},
        {"name": "longitude", "type": "double", "doc": "Driver's last known GPS longitude."},
        {"name": "status", "type": {
            "type": "enum",
            "name": "DriverStatus",
            "symbols": ["AVAILABLE", "UNAVAILABLE", "ON_RIDE", "OFFLINE"]
        }, "doc": "Driver's availability status."}
    ]
}


passenger_producer = EventHubProducerClient.from_connection_string(
    conn_str=CONNECTION_STRING, 
    eventhub_name=PASSENGER_EVENTHUB_NAME
)
driver_producer = EventHubProducerClient.from_connection_string(
    conn_str=CONNECTION_STRING, 
    eventhub_name=DRIVER_EVENTHUB_NAME
)

def store_passenger_request(record):
    try:
        # Serialize to AVRO
        bytes_writer = io.BytesIO()
        fastavro.schemaless_writer(bytes_writer, PASSENGER_REQUEST_SCHEMA, record)
        avro_data = bytes_writer.getvalue()
        
        # Send to EventHub
        event_data_batch = passenger_producer.create_batch()
        event_data_batch.add(EventData(avro_data))
        passenger_producer.send_batch(event_data_batch)
        print(f"[EventHub] Sent passenger request {record['request_id']}")
    except Exception as e:
        print(f"[EventHub] Error: {e}")


def store_driver_update(record):
    try:
        # Serialize to AVRO
        bytes_writer = io.BytesIO()
        fastavro.schemaless_writer(bytes_writer, DRIVER_UPDATE_SCHEMA, record)
        avro_data = bytes_writer.getvalue()
        
        # Send to EventHub
        event_data_batch = driver_producer.create_batch()
        event_data_batch.add(EventData(avro_data))
        driver_producer.send_batch(event_data_batch)
        print(f"[EventHub] Sent driver update for {record['driver_id']}")
    except Exception as e:
        print(f"[EventHub] Error: {e}")



class City:
    def __init__(self, city_center, city_radius, drivers, passengers, base_speed=30):
        city_center = (float(city_center[0]), float(city_center[1]))
        self.city_center = city_center
        self.city_radius = city_radius
        self.drivers = drivers
        self.passengers = passengers
        self.base_speed = base_speed
        self.simulation_time = 0  # in minutes
        self.demand_multiplier = 1.0
        self.pricing_multiplier = 1.0
        self.speed_factor = 1.0
        self.base_lambda = 3
        self.lock = threading.Lock()

    def update_demand_and_pricing(self):
        minutes_in_day = self.simulation_time % (24 * 60)
        hour = minutes_in_day // 60
        if 7 <= hour < 9 or 17 <= hour < 19:
            base_lambda = 10
            base_speed_factor = 0.7
        else:
            base_lambda = 3
            base_speed_factor = 1.0
        poisson_demand = np.random.poisson(base_lambda)
        self.demand_multiplier = max(1.0, 1.0 + (poisson_demand - base_lambda) / base_lambda)
        self.pricing_multiplier = self.demand_multiplier
        self.speed_factor = base_speed_factor
        self.base_lambda = base_lambda
        print(f"[Demand Update] Time: {hour:02d}:00, Poisson Demand: {poisson_demand}, "
              f"Demand Multiplier: {self.demand_multiplier:.2f}, "
              f"Pricing Multiplier: {self.pricing_multiplier:.2f}, "
              f"Speed Factor: {self.speed_factor:.2f}, Base Lambda: {self.base_lambda}")

    def update_driver_workforce(self):
        minutes_in_day = self.simulation_time % (24 * 60)
        hour = minutes_in_day // 60
        if hour < 6 or hour >= 22:
            offline_prob = 0.03
            online_prob = 0.005
        elif 6 <= hour < 10:
            offline_prob = 0.01
            online_prob = 0.02
        else:
            offline_prob = 0.015
            online_prob = 0.01
        with self.lock:
            for driver in self.drivers:
                if driver.status in ("AVAILABLE", "ON_RIDE"):
                    if random.random() < offline_prob:
                        driver.status = "OFFLINE"
                        print(f"[Driver Workforce] {driver.driver_id} went OFFLINE.")
                elif driver.status == "OFFLINE":
                    if random.random() < online_prob:
                        driver.status = "AVAILABLE"
                        print(f"[Driver Workforce] {driver.driver_id} came ONLINE.")

    def calculate_distance(self, loc1, loc2):
        lat1, lon1 = loc1
        lat2, lon2 = loc2
        lat_diff = (lat2 - lat1) * 111
        lon_diff = (lon2 - lon1) * 111 * math.cos(math.radians((lat1 + lat2) / 2))
        return math.sqrt(lat_diff ** 2 + lon_diff ** 2)

    def select_closest_driver(self, pickup_location, request_start_time, desired_vehicle_type, max_wait_time=None):
        if max_wait_time is None:
            max_wait_time = random.randint(5, 10)
        while True:
            with self.lock:
                closest_driver = None
                min_distance = float('inf')
                for driver in self.drivers:
                    # Only consider drivers with matching vehicle type who are AVAILABLE
                    if driver.status == "AVAILABLE" and driver.vehicle_type == desired_vehicle_type:
                        driver_loc = (driver.current_lat, driver.current_lon)
                        dist = self.calculate_distance(pickup_location, driver_loc)
                        if dist < min_distance:
                            min_distance = dist
                            closest_driver = driver
                if closest_driver:
                    closest_driver.status = "ON_RIDE"
                    print(f"[Driver Assigned] {closest_driver.driver_id} with {desired_vehicle_type} assigned for pickup at {pickup_location}.")
                    return closest_driver
            if time.time() - request_start_time > max_wait_time:
                print(f"[Queue] Passenger left the queue due to excessive wait time (no matching {desired_vehicle_type} driver available).")
                return None
            print(f"[Driver Queue] No available driver with type {desired_vehicle_type}. Waiting...")
            time.sleep(1)

    def calculate_trip_details(self, pickup_location, dropoff_location):
        distance = self.calculate_distance(pickup_location, dropoff_location)
        trip_duration_sec = (distance / (self.base_speed * self.speed_factor)) * 3600
        base_fare = 2.5
        per_km_rate = 1.5
        fare = (base_fare + per_km_rate * distance) * self.pricing_multiplier * self.demand_multiplier
        return distance, trip_duration_sec, fare

    def simulate_ride(self, request, driver):
        pickup_dict = request['pickup_location']
        dropoff_dict = request['dropoff_location']
        pickup_loc = (pickup_dict['latitude'], pickup_dict['longitude'])
        dropoff_loc = (dropoff_dict['latitude'], dropoff_dict['longitude'])
        driver_loc = (driver.current_lat, driver.current_lon)
        print(f"[Ride Start] {driver.driver_id} is heading to pickup location {pickup_dict} for passenger {request['passenger_id']}.")
        distance_to_pickup = self.calculate_distance(pickup_loc, driver_loc)
        travel_time_to_pickup = (distance_to_pickup / (self.base_speed * self.speed_factor)) * 3600
        print(f"[Pickup] {driver.driver_id} is {distance_to_pickup:.2f} km away; estimated time: {travel_time_to_pickup:.2f} sec.")
        time.sleep(travel_time_to_pickup * 0.01)
        with self.lock:
            driver.current_lat = pickup_dict['latitude']
            driver.current_lon = pickup_dict['longitude']
        print(f"[Pickup Complete] {driver.driver_id} has reached the pickup location.")
        distance, trip_duration_sec, fare = self.calculate_trip_details(pickup_loc, dropoff_loc)
        print(f"[Trip Details] Distance: {distance:.2f} km, Trip Time: {trip_duration_sec:.2f} sec, Estimated Fare: {fare:.2f}.")
        time.sleep(trip_duration_sec * 0.01)
        with self.lock:
            driver.current_lat = dropoff_dict['latitude']
            driver.current_lon = dropoff_dict['longitude']
            driver.status = "AVAILABLE"
        print(f"[Trip Complete] {driver.driver_id} has dropped off passenger {request['passenger_id']} at {dropoff_dict}.")
        passenger_request_record = {
            "request_id": request["request_id"],
            "passenger_id": request["passenger_id"],
            "timestamp": request["timestamp"],
            "pickup_location": request["pickup_location"],
            "dropoff_location": request["dropoff_location"],
            "vehicle_type": request["vehicle_type"],
            "passenger_preferences": request["passenger_preferences"],
            "payment_info": request["payment_info"],
            "estimated_fare": float(fare),
            "text_messages": request["text_messages"],
            "driver_rating": request["driver_rating"]
        }
        driver_update_record = {
            "driver_id": driver.driver_id,
            "timestamp": int(time.time() * 1000),
            "latitude": driver.current_lat,
            "longitude": driver.current_lon,
            "status": driver.status
        }
        print(f"[Records] Passenger Request: {passenger_request_record}")
        print(f"[Records] Driver Update: {driver_update_record}")
        store_passenger_request(passenger_request_record)
        store_driver_update(driver_update_record)
        return passenger_request_record, driver_update_record

    def process_request(self, request):
        pickup_dict = request['pickup_location']
        pickup_tuple = (pickup_dict['latitude'], pickup_dict['longitude'])
        print(f"[Process Request] Received ride request {request['request_id']} from passenger {request['passenger_id']}.")
        self.update_demand_and_pricing()
        request_start_time = time.time()
        desired_vehicle_type = request["vehicle_type"]
        driver = self.select_closest_driver(pickup_tuple, request_start_time, desired_vehicle_type)
        if driver:
            ride_thread = threading.Thread(target=self.simulate_ride, args=(request, driver))
            ride_thread.start()
        else:
            print(f"[Process Request] Passenger {request['passenger_id']} canceled request {request['request_id']} due to wait timeout.")

    def run_simulation(self, duration_seconds=60, request_interval=2):
        print("[Simulation Start] Running simulation for", duration_seconds, "seconds.")
        start_time = time.time()
        while time.time() - start_time < duration_seconds:
            self.simulation_time += 1
            print(f"\n[Simulation Time] Minute {self.simulation_time}")
            self.update_demand_and_pricing()
            self.update_driver_workforce()

            # Snapshot: record status of all drivers
            with self.lock:
                working_count = sum(1 for d in self.drivers if d.status != "OFFLINE")
                total_drivers = len(self.drivers)
                print(f"[Snapshot] {working_count}/{total_drivers} drivers working.")
                for driver in self.drivers:
                    driver_update = driver.generate_driver_update()
                    store_driver_update(driver_update)

            # Slow down ride requests by scaling the Poisson parameter
            num_requests = np.random.poisson(self.base_lambda * 0.5)
            print(f"[New Requests] Generating {num_requests} ride request(s) this cycle.")
            for _ in range(num_requests):
                if self.passengers:
                    passenger = random.choice(self.passengers)
                    request = passenger.make_request()
                    print(f"[New Request] {request['request_id']} generated by passenger {request['passenger_id']}.")
                    self.process_request(request)
                else:
                    print("[New Request] No passengers available.")
            time.sleep(request_interval)
        print("[Simulation End] Simulation complete.")

class Passenger:
    def __init__(self, passenger_id, city_center, city_radius):
        city_center = (float(city_center[0]), float(city_center[1]))
        self.passenger_id = passenger_id
        self.city_center = city_center
        self.city_radius = city_radius
        self.name = f"Passenger {passenger_id}"
        self.home = {"latitude": city_center[0] + random.uniform(-city_radius / 100, city_radius / 100),
                     "longitude": city_center[1] + random.uniform(-city_radius / 100, city_radius / 100)}
        self.work = {"latitude": city_center[0] + random.uniform(-city_radius / 100, city_radius / 100),
                     "longitude": city_center[1] + random.uniform(-city_radius / 100, city_radius / 100)}

    def make_request(self):
        if random.random() > 0.5:
            pickup = self.home
            dropoff = self.work
        else:
            pickup = self.work
            dropoff = self.home

        # Use weighted selection for vehicle types
        vehicle_types = ["ECONOMY", "LUXURY", "POOL", "SUV"]
        weights = [0.75, 0.1, 0.05, 0.1]  # Economy is much more likely (Note: extra weights beyond the list length are ignored)
        vehicle_type = random.choices(vehicle_types, weights=weights, k=1)[0]

        music_choices = ["NO_PREFERENCE", "POP", "ROCK", "CLASSICAL", "JAZZ", "HIP_HOP"]
        passenger_preferences = {
            "music": random.choice(music_choices),
            "temperature": random.randint(18, 26),
            "quiet_ride": random.choice([True, False])
        }
        payment_methods = ["CASH", "CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "APPLE_PAY", "GOOGLE_PAY"]
        payment_info = {
            "payment_method": random.choice(payment_methods),
            "coupon_codes": [] if random.random() >= 0.15 else [f"SAVE{random.randint(10,50)}"],
            "loyalty_points_used": random.randint(0, 100) if random.random() < 0.1 else None
        }
        request = {
            "request_id": f"REQ-{int(time.time())}-{random.randint(1000,9999)}",
            "passenger_id": self.passenger_id,
            "timestamp": int(time.time() * 1000),
            "pickup_location": pickup,
            "dropoff_location": dropoff,
            "vehicle_type": vehicle_type,
            "passenger_preferences": passenger_preferences,
            "payment_info": payment_info,
            "estimated_fare": 0.0,
            "text_messages": [],
            "driver_rating": round(random.uniform(1.0, 5.0), 1) if random.random() < 0.4 else None
        }
        if random.random() < 0.15:
            ai_content = generate_system_message(self.passenger_id)
            new_message = {
                "message_id": f"SYS-{int(time.time())}-{random.randint(1000,9999)}",
                "sender": "PASSENGER",
                "content": ai_content,
                "sent_at": int(time.time() * 1000)
            }
            request["text_messages"].append(new_message)

        print(f"[Make Request] Passenger {self.passenger_id} created request {request['request_id']}.")
        return request


class Driver:
    def __init__(self, driver_id, city_center, city_radius, vehicle_type=None):
        # Ensure city center coordinates are floats
        city_center = (float(city_center[0]), float(city_center[1]))
        self.driver_id = driver_id
        self.name = f"Driver {driver_id}"
        self.city_center = city_center
        self.city_radius = city_radius

        # Define possible vehicle types and choose one using weighted probabilities
        self.vehicle_types = ["ECONOMY", "LUXURY", "POOL", "SUV"]
        weights = [0.8, 0.08, 0.02, 0.1]
        self.vehicle_type = random.choices(self.vehicle_types, weights=weights, k=1)[0] if vehicle_type is None else vehicle_type

        # Initialize location near the city center
        self.current_lat = city_center[0] + random.uniform(-city_radius / 100, city_radius / 100)
        self.current_lon = city_center[1] + random.uniform(-city_radius / 100, city_radius / 100)
        
        # Randomly set initial status: 70% chance to start AVAILABLE, 30% OFFLINE
        self.status = "AVAILABLE" if random.random() < 0.7 else "OFFLINE"

        print(f"[Driver Init] {self.driver_id} initialized at ({self.current_lat:.4f}, {self.current_lon:.4f}) with status {self.status} and vehicle type {self.vehicle_type}.")

    def update_location(self, new_lat, new_lon):
        self.current_lat = new_lat
        self.current_lon = new_lon

    def update_status(self, new_status):
        self.status = new_status

    def simulate_movement(self, target_location, base_speed=30, speed_factor=1.0):
        # Calculate approximate distance (km) between current location and target
        lat_diff = (target_location["latitude"] - self.current_lat) * 111
        lon_diff = (target_location["longitude"] - self.current_lon) * 111 * math.cos(math.radians((self.current_lat + target_location["latitude"]) / 2))
        distance = math.sqrt(lat_diff ** 2 + lon_diff ** 2)
        # Calculate travel time (in seconds) and simulate movement with sleep
        travel_time_sec = (distance / (base_speed * speed_factor)) * 3600
        time.sleep(travel_time_sec * 0.01)
        self.update_location(target_location["latitude"], target_location["longitude"])

    def generate_driver_update(self):
        # Return a dictionary matching the AVRO schema for a driver update
        driver_update_record = {
            "driver_id": self.driver_id,
            "timestamp": int(time.time() * 1000),
            "latitude": self.current_lat,
            "longitude": self.current_lon,
            "status": self.status
        }
        return driver_update_record

if __name__ == "__main__":
    city_center = (40, -74)
    city_radius = 15
    drivers = [Driver(f"D{i:05d}", city_center, city_radius) for i in range(350)]
    passengers = [Passenger(f"P{i:05d}", city_center, city_radius) for i in range(650)]
    city = City(city_center, city_radius, drivers, passengers)
    city.run_simulation(duration_seconds=300, request_interval=2)
