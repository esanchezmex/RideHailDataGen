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

# Merge and clean
data = pd.merge(df_passengers, df_drivers, on="driver_id", how="left", suffixes=("", "_driver"))
data["status"] = data["status"].astype(str).str.upper()

# Streamlit UI
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

    st.subheader("Payment Method Distribution")
    if "payment_method" in data.columns:
        st.bar_chart(data["payment_method"].value_counts())

    
# 📊 Advanced Analytics
with advanced:
    st.subheader("Rating Distribution")
    if "driver_rating" in data.columns:
        st.bar_chart(data["driver_rating"].value_counts().sort_index())

    st.subheader("Outlier Detection: Long Rides")
    if "ride_duration" in data.columns:
        long_rides = data[data["ride_duration"] > data["ride_duration"].quantile(0.99)]
        st.write("Top 1% longest rides:")
        st.dataframe(long_rides[["request_id", "ride_duration", "status", "driver_id", "passenger_id"]])

# 📍 Location Maps
with maps:
    st.subheader("🔥 Pickup Heatmap")
    if {"pickup_latitude", "pickup_longitude"}.issubset(data.columns):
        pickup_points = data[["pickup_latitude", "pickup_longitude"]].dropna().rename(
            columns={"pickup_latitude": "lat", "pickup_longitude": "lon"}
        )
        pickup_heatmap = pdk.Layer(
            "HeatmapLayer",
            pickup_points,
            get_position='[lon, lat]',
            aggregation=pdk.types.String("SUM"),
            get_weight=1
        )
        view_pickup = pdk.ViewState(
            latitude=pickup_points["lat"].mean(),
            longitude=pickup_points["lon"].mean(),
            zoom=11
        )
        st.pydeck_chart(pdk.Deck(layers=[pickup_heatmap], initial_view_state=view_pickup))

    st.subheader("🔥 Dropoff Heatmap")
    if {"dropoff_latitude", "dropoff_longitude"}.issubset(data.columns):
        dropoff_points = data[["dropoff_latitude", "dropoff_longitude"]].dropna().rename(
            columns={"dropoff_latitude": "lat", "dropoff_longitude": "lon"}
        )
        dropoff_heatmap = pdk.Layer(
            "HeatmapLayer",
            dropoff_points,
            get_position='[lon, lat]',
            aggregation=pdk.types.String("SUM"),
            get_weight=1
        )
        view_dropoff = pdk.ViewState(
            latitude=dropoff_points["lat"].mean(),
            longitude=dropoff_points["lon"].mean(),
            zoom=11
        )
        st.pydeck_chart(pdk.Deck(layers=[dropoff_heatmap], initial_view_state=view_dropoff))

    st.subheader("🚦 Ride Route Paths")
    if {
        "pickup_latitude", "pickup_longitude",
        "dropoff_latitude", "dropoff_longitude"
    }.issubset(data.columns):
        routes = data[[
            "pickup_latitude", "pickup_longitude",
            "dropoff_latitude", "dropoff_longitude"
        ]].dropna().copy()

        routes = routes.rename(columns={
            "pickup_latitude": "start_lat", "pickup_longitude": "start_lng",
            "dropoff_latitude": "end_lat", "dropoff_longitude": "end_lng"
        })

        route_layer = pdk.Layer(
            "LineLayer",
            routes,
            get_source_position='[start_lng, start_lat]',
            get_target_position='[end_lng, end_lat]',
            get_width=1,
            get_color=[255, 0, 0],
            pickable=False
        )

        route_view = pdk.ViewState(
            latitude=routes["start_lat"].mean(),
            longitude=routes["start_lng"].mean(),
            zoom=11
        )

        st.pydeck_chart(pdk.Deck(layers=[route_layer], initial_view_state=route_view))
