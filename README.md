
# RideHailDataGen

**RideHailDataGen** is a Python-based simulator that generates realistic, event-driven data modeled after ride-hailing platforms like Uber and Lyft. It simulates a virtual city where drivers and passengers interact dynamically, emitting structured event streams to support the development and testing of real-time analytics pipelines.

## Purpose

RideHailDataGen enables teams to prototype and test stream processing architectures without relying on sensitive or live production data. By simulating key behaviors of a ride-hailing ecosystem at scale, it provides a reliable foundation for:

- Generating synthetic data for ride-hailing applications  
- Creating datasets for machine learning model training and testing  
- Simulating diverse supply-demand scenarios and rider behavior  
- Powering real-time stream ingestion, processing, and storage solutions  
- Supporting business-critical analytics  
- Driving dashboards and business insights to optimize ride-hailing operations

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

- `fastavro`: AVRO schema validation and serialization  
- `numpy`, `math`: Probabilistic modeling and calculations  
- `pandas`: Data structuring and time manipulation  
- `datetime`, `time`: Timestamp generation and delay control  
- `threading`: Concurrent event simulation  
- `json`: Serialization to JSON format  
- `os`, `shutil`, `glob`, `subprocess`: File system interactions and utility tasks  
- `getpass`: Credential handling for secure authentication  
- `confluent_kafka`: Kafka producer for stream publishing  
- `pyspark`: Spark Streaming for real-time data processing  
- `findspark`: Enables Spark usage within Jupyter/Colab environments  
- `streamlit`: Dashboarding (optional)  
- `plotly`: Visualization of metrics and geographic data  
- `azure-storage-blob`: Azure Blob Storage integration for storing stream outputs  

## Usage Guidance
To run, please begin by running the producer with the desired set of specifications. Please use the given schemas in order to run the producer without issues.
Proceed to run the consumer_WithPrints.ipynb to perform analytics from the data being generated and streamed. Then, run the consumerWithBlob.ipynb to save the output of the analytics to Blob storage.

Note: Keys have been made private for added security. Use the environment file to access them.

## File Explanations
### M1_01_driver_availability_schema.txt (Milestone 1)
This file defines the AVRO schema for driver availability updates. It captures each driver's ID, location (latitude and longitude), current status (e.g., AVAILABLE, ON_RIDE), and timestamp, enabling real-time tracking and operational analytics.

### M1_02_passenger_request_schema.txt (Milestone 1)
This file defines the AVRO schema for passenger ride requests. It includes identifiers, pickup/dropoff coordinates, vehicle preferences, passenger preferences (music, temperature, quiet ride), payment info, fare estimates, text message exchanges, and optional driver ratings. This schema enables simulation of realistic user behavior and supports in-depth analytics across request patterns, satisfaction, and communication flows.

### M1_03_generate_data.py (Milestone 1)
This script initializes and runs a full simulation of a virtual ride-hailing city. It creates dynamic passengers and drivers, simulates ride requests, driver movements, pricing updates, and traffic conditions. It generates and sends real-time passenger and driver events serialized in AVRO to Azure EventHub. AI-generated messages and AVRO schemas are included for realistic, analytics-ready data streaming.

### Producer.ipynb
This the data generation file from Milestone 1 but it is enhanced to integrate Spark and Kafka functionalities to send data to EventHub while keeping the realism from the original simulation. 

### ConsumerWithBlob.ipynb
The consumer takes data from EventHub and performs a serious of Spark SQL-based queries in order to generate value for our business. It proceeds to send those results to a Blob storage container to lay those results at rest.

### Consumer_WithPrints.ipynb
Then, it proceeds to print those results for user visualizaiton and send them to Streamlit for real-time visualization.

### dashboard.py
This Streamlit dashboard visualizes real-time analytics for the ride-hailing simulation. It integrates data from GitHub-hosted CSVs, displays key metrics like total rides and cancellations, and presents interactive visualizations using Plotly and Pydeck. The dashboard includes basic, intermediate, and advanced analytics, along with heatmaps and route maps for pickup and dropoff locations.

### drivers.csv
This file contains structured, simulation-generated data about driver profiles and ride activity. It includes fields such as `driver_id`, `vehicle_type`, `status`, and GPS coordinates. The file is automatically pushed from Azure Blob Storage to GitHub and is used by the Streamlit dashboard to display real-time driver-related analytics and visualizations.

### passengers.csv
This file stores simulation-generated passenger ride request data, including fields like `passenger_id`, `pickup` and `dropoff` coordinates, ride status, preferences, and payment methods. Like `drivers.csv`, it is automatically synced from Azure Blob Storage to GitHub to enable live data analysis within the Streamlit dashboard.

