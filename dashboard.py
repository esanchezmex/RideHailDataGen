import streamlit as st
import pandas as pd
import plotly.express as px
import time

# GitHub raw CSV URLs (replace with your actual GitHub URLs)
drivers_url = "https://raw.githubusercontent.com/your-username/your-repo/main/drivers.csv"
passengers_url = "https://raw.githubusercontent.com/your-username/your-repo/main/passengers.csv"

# Load data from GitHub
df_drivers = pd.read_csv(drivers_url)
df_passengers = pd.read_csv(passengers_url)

# Merge datasets (assumes 'ride_id' is common)
if 'ride_id' in df_drivers.columns and 'ride_id' in df_passengers.columns:
    data = pd.merge(df_passengers, df_drivers, on='ride_id', how='inner')
else:
    st.error("❌ ride_id column missing in one or both datasets.")
    st.stop()

# Filter
if "city" in data.columns:
    city_filter = st.selectbox("Select a City", data["city"].unique())
    data = data[data["city"] == city_filter]

st.subheader("📊 Key Metrics")
st.metric("Total Rides", len(data))
if 'status' in data.columns:
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
    if {'request_timestamp', 'accepted_timestamp', 'vehicle_type'}.issubset(data.columns):
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
    st.subheader("Demand vs Supply by Area")
    if 'area' in data.columns and 'status' in data.columns:
        demand = data[data['status'] == 'requested'].groupby('area').size()
        supply = data[data['status'] == 'available'].groupby('area').size()
        demand_supply = pd.DataFrame({"Demand": demand, "Supply": supply}).fillna(0)
        st.bar_chart(demand_supply)

    st.subheader("Vehicle Type Popularity vs Availability")
    if 'vehicle_type' in data.columns:
        request_counts = data[data['status'] == 'requested'].groupby('vehicle_type').size()
        available_counts = data[data['status'] == 'available'].groupby('vehicle_type').size()
        fleet_data = pd.DataFrame({"Requested": request_counts, "Available": available_counts}).fillna(0)
        st.bar_chart(fleet_data)

    st.subheader("Preferences vs Ratings")
    if {'temperature_pref', 'music_pref', 'quiet_ride', 'rating'}.issubset(data.columns):
        prefs_ratings = data.groupby(['temperature_pref', 'music_pref', 'quiet_ride'])['rating'].mean().reset_index()
        st.dataframe(prefs_ratings)

with advanced:
    st.subheader("Anomaly Detection in Ride Requests")
    if 'user_id' in data.columns:
        user_requests = data.groupby('user_id').size()
        suspicious_users = user_requests[user_requests > user_requests.quantile(0.95)]
        st.dataframe(suspicious_users)

    st.subheader("Surge Pricing Zone Prediction")
    if 'latitude' in data.columns and 'longitude' in data.columns:
        peak_data = data[(data['timestamp'].str.contains('17:|18:|19:')) & (data['status'] == 'requested')]
        st.map(peak_data[['latitude', 'longitude']])

    st.subheader("Fraud Detection")
    if 'ride_duration' in data.columns and 'payment_method' in data.columns:
        duration_outliers = data[data['ride_duration'] > data['ride_duration'].quantile(0.99)]
        suspicious_payments = data[data['payment_method'].isin(['unusual_card', 'unverified_wallet'])]
        st.dataframe(duration_outliers)
        st.dataframe(suspicious_payments)

# Sidebar refresh rate
refresh_rate = st.sidebar.slider("Auto-refresh rate (seconds)", 10, 120, 60)
st.sidebar.info("To apply the new refresh rate, rerun the app.")
