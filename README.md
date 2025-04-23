
# RideHailDataGen

**RideHailDataGen** is a Python-based simulator that generates realistic, event-driven data modeled after ride-hailing platforms like Uber and Lyft. It simulates a virtual city where drivers and passengers interact dynamically, emitting structured event streams to support the development and testing of real-time analytics pipelines.

## Purpose

RideHailDataGen enables teams to prototype and test stream processing architectures without relying on sensitive or live production data. By simulating key behaviors of a ride-hailing ecosystem at scale, it provides a reliable foundation for:

- Generating synthetic data for ride-hailing applications  
- Creating datasets for machine learning model training and testing  
- Simulating diverse supply-demand scenarios and rider behavior  
- Powering real-time stream ingestion, processing, and storage solutions  
- Supporting anomaly detection, surge pricing prediction, and other business-critical analytics  
- Driving dashboards and business insights to optimize ride-hailing operations

## Business Use Cases

This tool supports a wide range of analytics and operational insights, such as:

- **Demand Forecasting:** Predict future ride demand by time and location to optimize driver deployment  
- **Geo Heatmaps:** Visualize hotspots for ride requests, cancellations, and idle drivers  
- **Fleet Monitoring:** Track driver activity (idle, assigned, en route) in real time  
- **Cancellation Analysis:** Understand cancellation rates, causes (e.g., ETA, pricing), and user types  
- **Dynamic Pricing Testing:** Simulate pricing models under varying demand to validate surge logic  
- **Anomaly Detection:** Detect fraudulent patterns such as spoofed rides or excessive cancellations  
- **Response Time Metrics:** Measure time from ride request to driver assignment  
- **Streaming Dashboards:** Feed real-time metrics into BI platforms like Power BI or Grafana  

## Key Features

- Configurable virtual city with adjustable radius and population density  
- Heterogeneous driver fleet (Economy, Luxury, SUV, Pool)  
- Probabilistic rider preferences and time-based behavior changes  
- Time-of-day traffic modeling with surge simulation  
- AI-generated rider text messages using the OpenAI API  
- Real-time serialization in both AVRO and JSON formats  
- Multi-threaded simulation for realistic concurrent behavior  

## Passenger and Driver Schemas

**Passenger Request Schema:** Includes pickup/dropoff coordinates, vehicle type, passenger preferences (music, temperature, quiet ride), payment method, loyalty use, AI-generated messages, and ride status lifecycle fields. It supports deep analytics and realistic passenger behavior modeling.

**Driver Status Schema:** Captures geolocation and availability updates in real time. Includes driver ID, GPS coordinates, status (AVAILABLE, UNAVAILABLE, ON_RIDE, OFFLINE), and timestamp—ideal for fleet tracking and real-time map visualizations.

## Data Generator

The data generator simulates interactions between passengers and drivers. It:

- Initializes a virtual city with configurable population and radius  
- Randomly assigns passengers and drivers with behavioral models  
- Generates ride requests, driver updates, cancellations, messages, and status changes  
- Matches drivers to requests using geospatial logic  
- Serializes events to both AVRO and JSON in real time  
- Runs with threading to simulate realistic concurrency and load  
- Allows configuration for simulation time, event frequency, and behavior probabilities  

## EventHub Integration

**Producer:** The simulator sends events to Azure EventHub in real time. Each stream (passenger, driver) uses a dedicated EventHub or partition. Messages are batched and transmitted using the Azure SDK with schema metadata and binary payloads.

**Consumer:** Spark Streaming jobs in Google Colab consume the data from EventHub. These jobs decode the AVRO/JSON messages, apply transformations, and perform analytics or route data to storage. The pipeline supports windowing, aggregation, and real-time insight generation with built-in fault tolerance and checkpointing.

## Dependencies

- `openai`: For generating realistic passenger messages  
- `fastavro`: AVRO schema validation and serialization  
- `numpy`, `pandas`: Time-series simulation and probabilistic modeling  
- `streamlit`: Interactive dashboard for monitoring and visualization  
- `plotly`: Interactive geographic and temporal charts  
- `azure-storage-blob`: Integration with Azure Blob Storage for stream output  
- `threading`: Enables concurrent simulation of multiple users and events  

## Usage Example

```python
city_center = (40, -74)  # NYC-like coordinates
city_radius = 15         # in kilometers
drivers = [Driver(f"D{i:05d}", city_center, city_radius) for i in range(350)]
passengers = [Passenger(f"P{i:05d}", city_center, city_radius) for i in range(650)]
city = City(city_center, city_radius, drivers, passengers)
city.run_simulation(duration_seconds=300, request_interval=2)
```
