
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


