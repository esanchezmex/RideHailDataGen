# RideHailDataGen
RideHailDataGen is a Python-based tool for generating realistic ride-hailing service data (similar to Uber or Lyft). It creates a simulated city environment with drivers and passengers, and produces structured data about ride requests, driver movements, and interactions.

## Purpose
This tool is designed for:
- Generating test data for ride-hailing applications
- Creating datasets for machine learning models
- Simulating driver-passenger scenarios
- Analyzing patterns in ride-hailing services

##Features
- Simulates a dynamic city environment with configurable parameters
- Generates drivers with different vehicle types (Economy, Luxury, Pool, SUV)
- Creates passengers with randomized preferences
- Models time-of-day effects on traffic and demand
- Produces realistic driver movement patterns
- Generates AI-powered passenger text messages
- Records data in both JSON and Avro formats

## How It Works
### Core Components
- **City**: Central simulation environment with demand modeling
- **Driver**: Represents vehicle operators with location, status, and vehicle type
- **Passenger**: Simulates users with preferences and home/work locations

### Simulation Process
- Initializes a city with drivers and passengers
- Updates demand and pricing based on time of day
- Generates ride requests from passengers
- Matches requests with available drivers
- Simulates pickup and dropoff
- Records all transactions and updates

### Data Generation
The system outputs two main data streams:
- **Passenger Requests**: Complete ride details including preferences and messages
- **Driver Updates**: Location and status information for all drivers

### Notable Features
- Time-based demand fluctuation (rush hour peaks)
- AI-generated text messages between drivers and passengers
- Driver workforce modeling (drivers going online/offline)
- Location-based matching algorithm
- Dynamic pricing based on demand

### Dependencies
- OpenAI API for generating passenger messages
- fastavro for Avro data storage
- numpy for probability distributions
- threading for concurrent ride simulations (mostly for an occupied driver)

## Usage
All the user has to do is configure the city parameters, number of drivers and passengers, and run the simulation:

```python
city_center = (40, -74)
city_radius = 15  # km
drivers = [Driver(f"D{i:05d}", city_center, city_radius) for i in range(350)]
passengers = [Passenger(f"P{i:05d}", city_center, city_radius) for i in range(650)]
city = City(city_center, city_radius, drivers, passengers)
city.run_simulation(duration_seconds=300, request_interval=2)
```





