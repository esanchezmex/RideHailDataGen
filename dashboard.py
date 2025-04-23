import streamlit as st
import pandas as pd

# GitHub raw CSV URLs
drivers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/drivers.csv"
passengers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/passengers.csv"

# Load CSVs
df_drivers = pd.read_csv(drivers_url)
df_passengers = pd.read_csv(passengers_url)

# Merge on driver_id
data = pd.merge(df_passengers, df_drivers, on="driver_id", how="left")

# Normalize the status values to uppercase
data["status"] = data["status"].astype(str).str.upper()

# Streamlit layout
st.set_page_config(page_title="Ride-Hailing Dashboard", layout="wide")
st.title("🚖 Ride-Hailing Analytics Dashboard")

# Metrics
st.header("📊 Key Metrics")
total_rides = len(data)
completed_rides = len(data[data["status"] == "COMPLETED"])
cancelled_rides = len(data[data["status"] == "CANCELLED"])
cancel_rate = (cancelled_rides / total_rides * 100) if total_rides > 0 else 0

st.metric("Total Rides", total_rides)
st.metric("Completed Rides", completed_rides)
st.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# Tabs
basic, intermediate, advanced = st.tabs(["Basic Analytics", "Intermediate Analytics", "Advanced Analytics"])

with basic:
    st.subheader("Rides by Status")
    st.bar_chart(data["status"].value_counts())

    st.subheader("Rides by Vehicle Type")
    if "vehicle_type" in data.columns:
        st.bar_chart(data["vehicle_type"].value_counts())

with intermediate:
    st.subheader("Average Ride Duration by Vehicle Type")
    if "duration" in data.columns and "vehicle_type" in data.columns:
        avg_duration = data.groupby("vehicle_type")["duration"].mean()
        st.bar_chart(avg_duration)

    st.subheader("Payment Method Distribution")
    if "payment_method" in data.columns:
        st.bar_chart(data["payment_method"].value_counts())

with advanced:
    st.subheader("Rating Distribution")
    if "rating" in data.columns:
        st.bar_chart(data["rating"].value_counts().sort_index())

    st.subheader("Outlier Detection: Long Rides")
    if "duration" in data.columns:
        long_rides = data[data["duration"] > data["duration"].quantile(0.99)]
        st.write("Top 1% longest rides:")
        st.dataframe(long_rides[["ride_id", "duration", "status", "driver_id", "passenger_
