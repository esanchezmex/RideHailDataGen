import streamlit as st
import os
import pandas as pd
import plotly.express as px
from azure.storage.blob import BlobServiceClient
import io
import time

# Azure Blob Storage Configuration
AZURE_CONNECTION_STRING = os.environ.get("AZURE_CONNECTION_STRING")
CONTAINER_NAME = os.environ.get("CONTAINER_NAME")
BLOB_NAME = os.environ.get("BLOB_NAME")

# Function to load data from Azure Blob Storage or fallback to CSV
def load_data():
    try:
        if AZURE_CONNECTION_STRING and CONTAINER_NAME and BLOB_NAME:
            blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
            blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=BLOB_NAME)
            download_stream = blob_client.download_blob()
            return pd.read_parquet(io.BytesIO(download_stream.readall()))
        else:
            raise ValueError("Missing Azure config")
    except Exception as e:
        st.warning(f"⚠️ Falling back to sample CSV. Reason: {e}")
        return pd.read_csv("sample_rides.csv")

# Load data
data = load_data()

# Filters
if "city" in data.columns:
    city_filter = st.selectbox("Select a City", data["city"].unique())
    data = data[data["city"] == city_filter]

st.subheader("📊 Key Metrics")
st.metric("Total Rides", len(data))
st.metric("Completed Rides", len(data[data['status'] == "completed"]))
cancel_rate = (len(data[data['status'] == 'cancelled']) / len(data)) * 100 if len(data) > 0 else 0
st.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# Tabs for analytics
basic, intermediate, advanced = st.tabs(["Basic Analytics", "Intermediate Analytics", "Advanced Analytics"])

with basic:
    st.subheader("Rides per Hour (Tumbling Window)")
    data['hour'] = pd.to_datetime(data['timestamp']).dt.floor('H')
    hourly_rides = data.groupby(['hour', 'status']).size().unstack(fill_value=0)
    st.bar_chart(hourly_rides)

    st.subheader("Average Driver Response Time by Vehicle Type (15-min Hopping Window)")
    if 'request_timestamp' in data.columns and 'accepted_timestamp' in data.columns and 'vehicle_type' in data.columns:
        data["request_timestamp"] = pd.to_datetime(data["request_timestamp"])
        data["accepted_timestamp"] = pd.to_datetime(data["accepted_timestamp"])
        data["response_time"] = (data["accepted_timestamp"] - data["request_timestamp"]).dt.total_seconds() / 60
        data["window"] = data["request_timestamp"].dt.floor('15min')
        avg_response = data.groupby(['window', 'vehicle_type'])['response_time'].mean().reset_index()
        st.line_chart(avg_response.pivot(index='window', columns='vehicle_type', values='response_time'))

    st.subheader("Ride Duration by Time of Day")
    if 'ride_duration' in data.columns:
        data['time_of_day'] = pd.to_datetime(data['timestamp']).dt.hour
        avg_durations = data.groupby('time_of_day')['ride_duration'].mean()
        st.bar_chart(avg_durations)

with intermediate:
    st.subheader("Demand vs Supply by Area (Session-Based)")
    if 'area' in data.columns and 'status' in data.columns:
        demand = data[data['status'] == 'requested'].groupby('area').size()
        supply = data[data['status'] == 'available'].groupby('area').size()
        demand_supply = pd.DataFrame({"Demand": demand, "Supply": supply}).fillna(0)
        st.bar_chart(demand_supply)

    st.subheader("Vehicle Type Popularity vs Availability")
    request_counts = data[data['status'] == 'requested'].groupby('vehicle_type').size()
    available_counts = data[data['status'] == 'available'].groupby('vehicle_type').size()
    fleet_data = pd.DataFrame({"Requested": request_counts, "Available": available_counts}).fillna(0)
    st.bar_chart(fleet_data)

    st.subheader("Preferences vs Ratings (Sliding Window)")
    if 'temperature_pref' in data.columns and 'music_pref' in data.columns and 'quiet_ride' in data.columns and 'rating' in data.columns:
        prefs_ratings = data.groupby(['temperature_pref', 'music_pref', 'quiet_ride'])['rating'].mean().reset_index()
        st.dataframe(prefs_ratings)

with advanced:
    st.subheader("Anomaly Detection in Ride Requests")
    user_requests = data.groupby('user_id').size()
    suspicious_users = user_requests[user_requests > user_requests.quantile(0.95)]
    st.write("Users with unusually high number of requests:")
    st.dataframe(suspicious_users)

    st.subheader("Surge Pricing Zone Prediction")
    if 'latitude' in data.columns and 'longitude' in data.columns:
        peak_data = data[(data['timestamp'].str.contains('17:|18:|19:')) & (data['status'] == 'requested')]
        st.map(peak_data[['latitude', 'longitude']])

    st.subheader("Fraud Detection: Payment & Duration Outliers")
    if 'ride_duration' in data.columns and 'payment_method' in data.columns:
        duration_outliers = data[data['ride_duration'] > data['ride_duration'].quantile(0.99)]
        suspicious_payments = data[data['payment_method'].isin(['unusual_card', 'unverified_wallet'])]
        st.write("Outlier Rides:")
        st.dataframe(duration_outliers)
        st.write("Suspicious Payment Methods:")
        st.dataframe(suspicious_payments)

# Sidebar: Refresh interval
refresh_rate = st.sidebar.slider("Auto-refresh rate (seconds)", 10, 120, 60)
st.sidebar.info("To apply the new refresh rate, rerun the app.")
