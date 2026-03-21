import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import time

# --- CONNECT TO DATABASE ---
# We use 'postgres' (the service name) instead of 'localhost'
DB_URL = "postgresql://crypto_user:crypto_pass@postgres:5432/crypto_db"

st.set_page_config(page_title="Crypto Dashboard", layout="wide")

def get_data():
    """Fetch the latest Bitcoin data from Postgres"""
    try:
        engine = create_engine(DB_URL)
        # Get the last 50 entries
        query = "SELECT * FROM bitcoin_realtime ORDER BY fetched_at DESC LIMIT 50;"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# --- THE DASHBOARD ---
st.title("⚡ Real-Time Bitcoin Analytics")

placeholder = st.empty()

while True:
    df = get_data()
    
    if not df.empty:
        with placeholder.container():
            # Calculate metrics
            latest_price = df.iloc[0]['price_usd']
            latest_time = df.iloc[0]['fetched_at']
            
            # Display KPIs
            col1, col2 = st.columns(2)
            col1.metric("Current Price", f"${latest_price:,.2f}")
            col2.metric("Last Updated", str(latest_time))
            
            # Display Chart
            fig = px.line(df, x='fetched_at', y='price_usd', title='Bitcoin Price History')
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")
    # Refresh every 10 seconds
    time.sleep(10)