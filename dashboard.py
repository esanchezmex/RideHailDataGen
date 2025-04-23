import pandas as pd
import streamlit as st

# GitHub raw URLs
drivers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/drivers.csv"
passengers_url = "https://raw.githubusercontent.com/esanchezmex/RideHailDataGen/main/passengers.csv"

# Load data
df_drivers = pd.read_csv(drivers_url)
df_passengers = pd.read_csv(passengers_url)

# Merge on driver_id
data = pd.merge(df_passengers, df_drivers, on='driver_id', how='left')

# Normalize status field
if 'status_passenger' in data.columns:
    data['status_passenger'] = data['status_passenger'].astype(str).str.strip().str.lower()

# Streamlit layout
st.set_page_config(layout="wide")
st.title("🚕 Ride Hailing Analytics Dashboard")

# Metrics section
st.header("📊 Key Metrics")
total_rides = len(data)
completed_rides = len(data[data['status_passenger'] == "completed"])
cancelled_rides = len(data[data['status_passenger'] == "cancelled"])
cancel_rate = (cancelled_rides / total_rides * 100) if total_rides > 0 else 0

st.metric("Total Rides", total_rides)
st.metric("Completed Rides", completed_rides)
st.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# Tabs
tab1, tab2, tab3 = st.tabs(["Basic Analytics", "Intermediate Analytics", "Advanced Analytics"])

# Basic Analytics
with tab1:
    st.subheader("📌 Rides by Status")
    if 'status_passenger' in data.columns:
        st.bar_chart(data['status_passenger'].value_counts())

# Intermediate Analytics
with tab2:
    st.subheader("📍 Demand vs Supply by Area")
    if 'area' in data.columns and 'status_passenger' in data.columns:
        demand_supply = data[data['status_passenger'].isin(['requested', 'available'])].groupby(
            ['area', 'status_passenger']).size().unstack(fill_value=0)
        st.bar_chart(demand_supply)

# Advanced Analytics
with tab3:
    st.subheader("🔍 Ratings and Preferences")
    if 'rating' in data.columns:
        st.line_chart(data['rating'].dropna().rolling(100).mean())
