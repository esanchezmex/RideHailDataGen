import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

# GitHub CSV URLs
drivers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/drivers.csv"
passengers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/passengers.csv"

# Load data
df_drivers = pd.read_csv(drivers_url)
df_passengers = pd.read_csv(passengers_url)

# Merge
data = pd.merge(df_passengers, df_drivers, on="driver_id", how="left", suffixes=("", "_driver"))

# Cleanup
data["status"] = data["status"].astype(str).str.upper()

# Setup Streamlit
st.set_page_config(page_title="Ride-Hailing Dashboard", layout="wide")
st.title("🚖 Ride-Hailing Analytics Dashboard")

# 📊 Key Metrics
st.header("📊 Key Metrics")
total_rides = len(data)
completed_rides = len(data[data["status"] == "COMPLETED"])
cancelled_rides = len(data[data["status"] == "CANCELLED"])
cancel_rate = (cancelled_rides / total_rides * 100) if total_rides > 0 else 0

st.metric("Total Rides", total_rides)
st.metric("Completed Rides", completed_rides)
st.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# 📁 Tabs
basic, intermediate, advanced, maps = st.tabs([
    "Basic Analytics", "Intermediate Analytics", "Advanced Analytics", "📍 Location Maps"
])

# 📊 Basic Analytics
with basic:
    st.subheader("Rides by Status")
    st.bar_chart(data["status"].value_counts())

    st.subheader("Rides by Vehicle Type")
    if "vehicle_type" in data.columns:
        st.bar_chart(data["vehicle_type"].value_counts())

# 📈 Intermediate Analytics
with intermediate:
    st.subheader("Average Ride Duration by Vehicle Type")
    if "ride_duration" in data.columns and "vehicle_type" in data.columns:
        avg_duration = data.groupby("vehicle_type")["ride_duration"].mean()
        st.bar_chart(avg_duration)

    st.subheader("
