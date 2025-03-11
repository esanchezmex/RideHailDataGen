import json
import random
import time
from datetime import datetime
import io
import numpy as np
import pandas as pd
from mimesis import Person, Address, Datetime, Transport, Text
from mimesis.locales import Locale
import fastavro

# Create Mimesis generators
person = Person(locale=Locale.EN)
address = Address(locale=Locale.EN)
datetime_gen = Datetime(locale=Locale.EN)
transport = Transport()
text = Text(locale=Locale.EN)

class RideHailingDataGenerator:
    def __init__(self, 
                 num_drivers=100, 
                 num_passengers=500,
                 city_center_lat=40.7128, 
                 city_center_lon=-74.0060,
                 city_radius=10,
                 demand_level="normal",
                 pricing_model="standard",
                 surge_multiplier_range=(1.0, 2.5),
                 vehicle_type_distribution=None,
                 driver_availability_percentage=70,
                 rush_hour_times=((7, 9), (17, 19)),
                 rush_hour_probability_multiplier=2.0):
        """
        Initialize the ride-hailing data generator with configurable parameters.
        
        Parameters:
        -----------
        num_drivers : int
            Number of active drivers in the system
        num_passengers : int
            Number of potential passengers in the system
        city_center_lat : float
            Latitude of city center
        city_center_lon : float
            Longitude of city center
        city_radius : float
            Approximate radius of the city in kilometers
        demand_level : str
            Level of ride demand - "low", "normal", "high", "extreme"
        pricing_model : str
            Pricing strategy - "standard", "dynamic", "flat", "distance_heavy"
        surge_multiplier_range : tuple
            Min and max range for surge pricing multiplier (e.g., (1.0, 2.5))
        vehicle_type_distribution : dict
            Distribution of vehicle types (e.g., {"ECONOMY": 0.5, "STANDARD": 0.3, ...})
        driver_availability_percentage : int
            Percentage of drivers available (0-100)
        rush_hour_times : tuple of tuples
            Tuples of (start_hour, end_hour) for morning and evening rush hours
        rush_hour_probability_multiplier : float
            How much more likely requests are during rush hours
        """
        self.num_drivers = num_drivers
        self.num_passengers = num_passengers
        self.city_center = (city_center_lat, city_center_lon)
        self.city_radius = city_radius
        
        # Configure demand level
        self.demand_level = demand_level
        self.demand_multipliers = {
            "low": 0.5,
            "normal": 1.0,
            "high": 2.0,
            "extreme": 4.0
        }
        
        # Configure pricing model
        self.pricing_model = pricing_model
        self.pricing_models = {
            "standard": {"base": 2.5, "per_km": 1.5, "per_min": 0.3},
            "dynamic": {"base": 2.0, "per_km": 1.8, "per_min": 0.4, "demand_factor": 0.2},
            "flat": {"base": 8.0, "per_km": 0.8, "per_min": 0.2},
            "distance_heavy": {"base": 1.5, "per_km": 2.5, "per_min": 0.1}
        }
        
        # Configure surge pricing
        self.surge_multiplier_range = surge_multiplier_range
        
        # Configure vehicle distribution
        self.vehicle_types = ["ECONOMY", "STANDARD", "LUXURY", "POOL", "SUV", "ELECTRIC"]
        if vehicle_type_distribution:
            self.vehicle_type_distribution = vehicle_type_distribution
        else:
            # Default distribution
            self.vehicle_type_distribution = {
                "ECONOMY": 0.4,
                "STANDARD": 0.3,
                "LUXURY": 0.1,
                "POOL": 0.1,
                "SUV": 0.05,
                "ELECTRIC": 0.05
            }
        
        # Configure driver availability
        self.driver_availability_percentage = driver_availability_percentage
        
        # Configure rush hour settings
        self.rush_hour_times = rush_hour_times
        self.rush_hour_probability_multiplier = rush_hour_probability_multiplier
        
        # Initialize drivers and passengers
        self.init_drivers()
        self.init_passengers()
        
        # Load AVRO schemas
        self.passenger_request_schema = self.get_passenger_request_schema()
        self.driver_update_schema = self.get_driver_update_schema()
    
    def get_passenger_request_schema(self):
        schema = {
            "type": "record",
            "name": "PassengerRequest",
            "namespace": "com.example.ridehailing",
            "fields": [
                {"name": "request_id", "type": "string"},
                {"name": "passenger_id", "type": "string"},
                {"name": "timestamp", "type": "long"},
                {"name": "pickup_location", "type": {
                    "type": "record", "name": "Location", "fields": [
                        {"name": "latitude", "type": "double"},
                        {"name": "longitude", "type": "double"}
                    ]
                }},
                {"name": "dropoff_location", "type": "Location"},
                {"name": "vehicle_type", "type": {
                    "type": "enum", "name": "VehicleType", 
                    "symbols": ["ECONOMY", "STANDARD", "LUXURY", "POOL", "SUV", "ELECTRIC"]
                }},
                {"name": "passenger_preferences", "type": {
                    "type": "record", "name": "PassengerPreferences", "fields": [
                        {"name": "music", "type": {
                            "type": "enum", "name": "MusicPreference",
                            "symbols": ["NO_PREFERENCE", "POP", "ROCK", "CLASSICAL", "JAZZ", "HIP_HOP"]
                        }, "default": "NO_PREFERENCE"},
                        {"name": "temperature", "type": "int", "default": 22},
                        {"name": "quiet_ride", "type": "boolean", "default": False}
                    ]
                }},
                {"name": "payment_info", "type": {
                    "type": "record", "name": "PaymentInfo", "fields": [
                        {"name": "payment_method", "type": {
                            "type": "enum", "name": "PaymentMethod",
                            "symbols": ["CASH", "CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "APPLE_PAY", "GOOGLE_PAY"]
                        }},
                        {"name": "coupon_codes", "type": {"type": "array", "items": "string"}, "default": []},
                        {"name": "loyalty_points_used", "type": ["null", "int"], "default": None}
                    ]
                }},
                {"name": "estimated_fare", "type": "float"},
                {"name": "text_messages", "type": {
                    "type": "array", "items": {
                        "type": "record", "name": "TextMessage", "fields": [
                            {"name": "message_id", "type": "string"},
                            {"name": "sender", "type": {
                                "type": "enum", "name": "SenderType", 
                                "symbols": ["DRIVER", "PASSENGER", "SYSTEM"]
                            }},
                            {"name": "content", "type": "string"},
                            {"name": "sent_at", "type": "long"}
                        ]
                    }
                }, "default": []},
                {"name": "driver_rating", "type": ["null", "float"], "default": None}
            ]
        }
        return schema
    
    def get_driver_update_schema(self):
        schema = {
            "type": "record",
            "name": "DriverAvailabilityUpdate",
            "namespace": "com.yourcompany.ridehailing",
            "fields": [
                {"name": "driver_id", "type": "string"},
                {"name": "timestamp", "type": "long"},
                {"name": "latitude", "type": "double"},
                {"name": "longitude", "type": "double"},
                {"name": "status", "type": {
                    "type": "enum", "name": "DriverStatus",
                    "symbols": ["AVAILABLE", "UNAVAILABLE", "ON_RIDE", "OFFLINE"]
                }}
            ]
        }
        return schema
    
    def init_drivers(self):
        """Initialize driver data with configured availability percentage"""
        self.drivers = []
        for i in range(self.num_drivers):
            # Choose vehicle type based on configured distribution
            vehicle_type = self._weighted_choice(self.vehicle_type_distribution)
            
            # Set availability based on configured percentage
            is_available = random.random() < (self.driver_availability_percentage / 100)
            status = "AVAILABLE" if is_available else random.choice(["UNAVAILABLE", "ON_RIDE", "OFFLINE"])
            
            driver = {
                'driver_id': f"D{i:05d}",
                'name': person.full_name(),
                'vehicle_type': vehicle_type,
                'current_lat': self.city_center[0] + random.uniform(-self.city_radius/100, self.city_radius/100),
                'current_lon': self.city_center[1] + random.uniform(-self.city_radius/100, self.city_radius/100),
                'status': status
            }
            self.drivers.append(driver)
    
    def init_passengers(self):
        """Initialize passenger data"""
        self.passengers = []
        for i in range(self.num_passengers):
            passenger = {
                'passenger_id': f"P{i:05d}",
                'name': person.full_name(),
                'home': {
                    'latitude': self.city_center[0] + random.uniform(-self.city_radius/100, self.city_radius/100),
                    'longitude': self.city_center[1] + random.uniform(-self.city_radius/100, self.city_radius/100)
                },
                'work': {
                    'latitude': self.city_center[0] + random.uniform(-self.city_radius/100, self.city_radius/100),
                    'longitude': self.city_center[1] + random.uniform(-self.city_radius/100, self.city_radius/100)
                }
            }
            self.passengers.append(passenger)

    def _weighted_choice(self, weights_dict):
        """Choose an item based on weighted probabilities"""
        items = list(weights_dict.keys())
        weights = list(weights_dict.values())
        return random.choices(items, weights=weights, k=1)[0]
    
    def calculate_fare(self, distance_km, duration_min):
        """Calculate fare based on configured pricing model"""
        model = self.pricing_models[self.pricing_model]
        fare = model["base"] + (distance_km * model["per_km"]) + (duration_min * model["per_min"])
        
        # Apply surge based on time of day
        surge = self.calculate_surge_multiplier()
        
        # Add demand factor for dynamic pricing
        if self.pricing_model == "dynamic" and self.demand_level in ["high", "extreme"]:
            fare += model["demand_factor"] * self.demand_multipliers[self.demand_level]
        
        return fare * surge
    
    def calculate_surge_multiplier(self):
        """Calculate surge multiplier based on time and demand"""
        current_hour = datetime.now().hour
        
        # Check if current time is within rush hours
        is_rush_hour = False
        for start_hour, end_hour in self.rush_hour_times:
            if start_hour <= current_hour <= end_hour:
                is_rush_hour = True
                break
        
        # Base surge depends on demand level
        base_surge = 1.0
        if self.demand_level == "high":
            base_surge = 1.2
        elif self.demand_level == "extreme":
            base_surge = 1.5
        
        # Apply rush hour factor
        if is_rush_hour:
            surge = base_surge * random.uniform(
                self.surge_multiplier_range[0], 
                self.surge_multiplier_range[1]
            )
        else:
            surge = base_surge
        
        return surge
    
    def generate_passenger_request(self):
        """Generate a random passenger ride request with configured parameters"""
        passenger = random.choice(self.passengers)
        home_loc = passenger['home']
        work_loc = passenger['work']
        
        # Randomly choose either from home or to home
        if random.random() > 0.5:
            pickup = home_loc
            dropoff = {
                'latitude': self.city_center[0] + random.uniform(-self.city_radius/100, self.city_radius/100),
                'longitude': self.city_center[1] + random.uniform(-self.city_radius/100, self.city_radius/100)
            }
        else:
            pickup = {
                'latitude': self.city_center[0] + random.uniform(-self.city_radius/100, self.city_radius/100),
                'longitude': self.city_center[1] + random.uniform(-self.city_radius/100, self.city_radius/100)
            }
            dropoff = home_loc
        
        # Calculate distance and duration
        distance_km = self.calculate_distance(
            (pickup['latitude'], pickup['longitude']),
            (dropoff['latitude'], dropoff['longitude'])
        )
        
        # Estimate duration - affected by time of day
        current_hour = datetime.now().hour
        is_rush_hour = any(start <= current_hour <= end for start, end in self.rush_hour_times)
        
        # Base speed varies by time of day
        avg_speed_kmh = 20 if is_rush_hour else 30
        duration_min = (distance_km / avg_speed_kmh) * 60
        
        # Calculate fare based on pricing model
        estimated_fare = self.calculate_fare(distance_km, duration_min)
        
        # Choose vehicle type based on distribution
        vehicle_type = self._weighted_choice(self.vehicle_type_distribution)
        
        # Generate random passenger preferences
        music_prefs = ["NO_PREFERENCE", "POP", "ROCK", "CLASSICAL", "JAZZ", "HIP_HOP"]
        payment_methods = ["CASH", "CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "APPLE_PAY", "GOOGLE_PAY"]
        
        # Generate possible text messages
        text_messages = []
        if random.random() < 0.3:
            num_messages = random.randint(1, 3)
            for i in range(num_messages):
                message = {
                    "message_id": f"MSG-{int(time.time())}-{random.randint(1000, 9999)}",
                    "sender": random.choice(["DRIVER", "PASSENGER", "SYSTEM"]),
                    "content": text.sentence(),
                    "sent_at": int(time.time() * 1000) - random.randint(10000, 300000)
                }
                text_messages.append(message)
        
        # Create coupon codes (occasionally)
        coupon_codes = []
        if random.random() < 0.15:
            coupon_codes.append(f"SAVE{random.randint(10, 50)}")
        
        # Create the request according to the schema
        request = {
            "request_id": f"REQ-{int(time.time())}-{random.randint(1000, 9999)}",
            "passenger_id": passenger['passenger_id'],
            "timestamp": int(time.time() * 1000),
            "pickup_location": pickup,
            "dropoff_location": dropoff,
            "vehicle_type": vehicle_type,
            "passenger_preferences": {
                "music": random.choice(music_prefs),
                "temperature": random.randint(18, 26),
                "quiet_ride": random.choice([True, False])
            },
            "payment_info": {
                "payment_method": random.choice(payment_methods),
                "coupon_codes": coupon_codes,
                "loyalty_points_used": random.randint(0, 100) if random.random() < 0.1 else None
            },
            "estimated_fare": float(round(estimated_fare, 2)),
            "text_messages": text_messages,
            "driver_rating": round(random.uniform(1.0, 5.0), 1) if random.random() < 0.4 else None
        }
        
        return request
    
    def generate_driver_update(self):
        """Generate a driver status update that matches the schema"""
        driver = random.choice(self.drivers)
        
        # Update driver location with a small random movement
        new_lat = driver['current_lat'] + random.uniform(-0.002, 0.002)
        new_lon = driver['current_lon'] + random.uniform(-0.002, 0.002)
        
        # Sometimes change status
        if random.random() < 0.1:  # 10% chance to change status
            driver['status'] = random.choice(["AVAILABLE", "UNAVAILABLE", "ON_RIDE", "OFFLINE"])
        
        update = {
            "driver_id": driver['driver_id'],
            "timestamp": int(time.time() * 1000),
            "latitude": new_lat,
            "longitude": new_lon,
            "status": driver['status']
        }
        
        # Update driver in our local state
        driver['current_lat'] = new_lat
        driver['current_lon'] = new_lon
        
        return update
    
    def calculate_distance(self, point1, point2):
        """Calculate distance between two lat/lon points in kilometers"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # Very rough approximation (1 degree is approximately 111km)
        lat_diff = (lat2 - lat1) * 111
        lon_diff = (lon2 - lon1) * 111 * np.cos(np.radians((lat1 + lat2) / 2))
        
        return np.sqrt(lat_diff**2 + lon_diff**2)
    
    def serialize_to_json(self, data):
        """Serialize data to JSON"""
        return json.dumps(data)
    
    def serialize_to_avro(self, data, schema):
        """Serialize data to AVRO format"""
        bytes_writer = io.BytesIO()
        fastavro.schemaless_writer(bytes_writer, schema, data)
        return bytes_writer.getvalue()
    
    def run_simulation(self, duration_seconds=60, events_per_second=5):
        """Run a simulation generating events for a specified duration"""
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        passenger_requests = []
        driver_updates = []
        
        while time.time() < end_time:
            # Calculate how many events to generate this second
            num_events = np.random.poisson(events_per_second)
            
            for _ in range(num_events):
                if random.random() < 0.4:  # 40% chance for passenger request
                    request = self.generate_passenger_request()
                    passenger_requests.append(request)
                    print(f"Generated passenger request: {request['request_id']}")
                else:  # 60% chance for driver update
                    update = self.generate_driver_update()
                    driver_updates.append(update)
                    print(f"Generated driver update: {update['driver_id']}")
            
            # Sleep to simulate real-time
            time.sleep(1)
        
        print(f"Simulation complete. Generated {len(passenger_requests)} passenger requests and {len(driver_updates)} driver updates.")
        return passenger_requests, driver_updates
    
    def save_to_files(self, passenger_requests, driver_updates, format='json'):
        """Save generated data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            with open(f"passenger_requests_{timestamp}.json", 'w') as f:
                json.dump(passenger_requests, f, indent=2)
            
            with open(f"driver_updates_{timestamp}.json", 'w') as f:
                json.dump(driver_updates, f, indent=2)
                
        elif format == 'avro':
            # For AVRO, we need to use the fastavro writer
            with open(f"passenger_requests_{timestamp}.avro", 'wb') as f:
                fastavro.writer(f, self.passenger_request_schema, passenger_requests)
            
            with open(f"driver_updates_{timestamp}.avro", 'wb') as f:
                fastavro.writer(f, self.driver_update_schema, driver_updates)
        
        print(f"Data saved to files with timestamp {timestamp}")




if __name__ == "__main__":
    # Create generator for New York City
    generator = RideHailingDataGenerator(
        num_drivers=200,
        num_passengers=1000,
        city_center_lat=40.7128, 
        city_center_lon=-74.0060,
        city_radius=15
    )
    
    # Run a simulation for 5 minutes
    passenger_requests, driver_updates = generator.run_simulation(
        duration_seconds=300,
        events_per_second=10
    )
    
    # Save to both JSON and AVRO files
    generator.save_to_files(passenger_requests, driver_updates, format='json')
    generator.save_to_files(passenger_requests, driver_updates, format='avro')
    
    # Save sample of data as CSV for easy viewing
    pd.DataFrame(passenger_requests[:100]).to_csv("sample_passenger_requests.csv", index=False)
    pd.DataFrame(driver_updates[:100]).to_csv("sample_driver_updates.csv", index=False)