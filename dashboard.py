import streamlit as st
import pandas as pd
import plotly.express as px

# GitHub raw CSV URLs (replace with your actual data paths if changed)
drivers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/drivers.csv"
passengers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/passengers.csv"

# Load datasets
df_drivers = pd.read_csv(drivers_url)
df_passengers = pd.read_csv(passengers_url)

# Merge on driver_id
data = pd.merge(df_passengers, df_drivers, on="driver_id", how="inner", suffixes=("_passenger", "_driver"))

st.title("🚖 Ride-Hailing Analytics Dashboard")

# City filter
if "city" in data.columns:
    selected_city = st.selectbox("Select City", data["city"].dropna().unique())
    data = data[data["city"] == selected_city]

# Metrics
st.subheader("📊 Key Metrics")
st.metric("Total Rides", len(data))
if 'status_passenger' in data.columns:
    st.metric("Completed Rides", len(data[data['status_passenger'] == "completed"]))
    cancel_rate = (len(data[data['status_passenger'] == "cancelled"]) / len(data)) * 100
    st.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# Tabs
basic, intermediate, advanced = st.tabs(["Basic Analytics", "Intermediate Analytics", "Advanced Analytics"])

with basic:
    st.subheader("Rides per Hour")
    data["timestamp_passenger"] = pd.to_datetime(data["timestamp_passenger"])
    data["hour"] = data["timestamp_passenger"].dt.hour
    ride_counts = data.groupby(["hour", "status_passenger"]).size().unstack(fill_value=0)
    st.bar_chart(ride_counts)

    st.subheader("Driver Response Time by Vehicle Type")
    if {'request_timestamp', 'accepted_timestamp', 'vehicle_type'}.issubset(data.columns):
        data["request_timestamp"] = pd.to_datetime(data["request_timestamp"])
        data["accepted_timestamp"] = pd.to_datetime(data["accepted_timestamp"])
        data["response_time"] = (data["accepted_timestamp"] - data["request_timestamp"]).dt.total_seconds() / 60
        data["window"] = data["request_timestamp"].dt.floor("15min")
        response = data.groupby(["window", "vehicle_type"])["response_time"].mean().reset_index()
        st.line_chart(response.pivot(index="window", columns="vehicle_type", values="response_time"))

    st.subheader("Ride Duration by Hour")
    if "ride_duration" in data.columns:
        avg_dur = data.groupby(data["timestamp_passenger"].dt.hour)["ride_duration"].mean()
        st.bar_chart(avg_dur)

with intermediate:
    st.subheader("Demand vs Supply by Area")
    if "area" in data.columns:
        demand = data[data["status_passenger"] == "requested"].groupby("area").size()
        supply = data[data["status_passenger"] == "available"].groupby("area").size()
        summary = pd.DataFrame({"Demand": demand, "Supply": supply}).fillna(0)
        st.bar_chart(summary)

    st.subheader("Vehicle Type Popularity")
    requests = data[data["status_passenger"] == "requested"].groupby("vehicle_type").size()
    avail = data[data["status_passenger"] == "available"].groupby("vehicle_type").size()
    fleet = pd.DataFrame({"Requested": requests, "Available": avail}).fillna(0)
    st.bar_chart(fleet)

    st.subheader("Preferences vs Ratings")
    if {'temperature_pref', 'music_pref', 'quiet_ride', 'rating'}.issubset(data.columns):
        grouped = data.groupby(['temperature_pref', 'music_pref', 'quiet_ride'])['rating'].mean().reset_index()
        st.dataframe(grouped)

with advanced:
    st.subheader("Anomaly Detection")
    if "passenger_id" in data.columns:
        suspicious = data.groupby("passenger_id").size()
        st.dataframe(suspicious[suspicious > suspicious.quantile(0.95)])

    st.subheader("Surge Zone Mapping")
    if {'latitude', 'longitude'}.issubset(data.columns):
        surge = data[(data["timestamp_passenger"].dt.hour.isin([17, 18, 19])) & (data["status_passenger"] == "requested")]
        st.map(surge[["latitude", "longitude"]])

    st.subheader("Fraud Detection")
    if "ride_duration" in data.columns and "payment_method" in data.columns:
        outliers = data[data["ride_duration"] > data["ride_duration"].quantile(0.99)]
        suspicious = data[data["payment_method"].isin(["unusual_card", "unverified_wallet"])]
        st.dataframe(outliers)
        st.dataframe(suspicious)

# Sidebar refresh control
refresh = st.sidebar.slider("Auto-refresh rate (seconds)", 10, 120, 60)
st.sidebar.info("To apply changes, rerun the app.")
