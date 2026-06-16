from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from datetime import timedelta
import requests
import logging

# --- CONFIGURATION ---
CONN_ID = 'crypto_db'  
COIN_ID = 'btc-bitcoin'
# Fixed double interpolation string bug from original code
API_URL = f"https://api.coinpaprika.com/v1/tickers/{COIN_ID}"

default_args = {
    'owner': 'airflow',
    'retries': 2,                    # Bumped up to 2 for better transient error resilience
    'retry_delay': timedelta(minutes=1),
}

def extract_and_load_data(**kwargs):
    """
    Fetches data from Coinpaprika and upserts it deterministically into Postgres.
    """
    # 1. DETERMINISTIC CONTEXT (Capture Airflow's execution window timestamp)
    # This prevents using live system time, allowing flawless backfills/retries
    logical_fetch_time = kwargs['data_interval_start']
    logging.info(f"Executing task for scheduled window start time: {logical_fetch_time}")

    # 2. EXTRACT (Get data from API)
    logging.info(f"Fetching data for {COIN_ID}...")
    response = requests.get(API_URL, timeout=15) # Added explicit network timeout safety
    response.raise_for_status()
    data = response.json()

    # 3. TRANSFORM (Select only what we need)
    symbol = data['symbol']
    price = data['quotes']['USD']['price']
    volume = data['quotes']['USD']['volume_24h']
    market_cap = data['quotes']['USD']['market_cap']

    logging.info(f"Price: ${price}, Volume: {volume}")

    # 4. LOAD (Idempotent Upsert into DB)
    pg_hook = PostgresHook(postgres_conn_id=CONN_ID)
    
    
    upsert_sql = """
        INSERT INTO bitcoin_realtime (symbol, price_usd, volume_24h, market_cap, fetched_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (symbol, fetched_at) 
        DO UPDATE SET 
            price_usd = EXCLUDED.price_usd,
            volume_24h = EXCLUDED.volume_24h,
            market_cap = EXCLUDED.market_cap;
    """
    
    # Passing logical_fetch_time explicitly as the 5th parameter
    parameters = (symbol, price, volume, market_cap, logical_fetch_time)
    
    pg_hook.run(upsert_sql, parameters=parameters)
    logging.info("Data successfully synchronized with Postgres safely (Idempotency guaranteed)!")

with DAG(
    dag_id="05_bitcoin_pipeline",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="*/5 * * * *", 
    catchup=False,
    tags=['crypto']
) as dag:

    # Task 1: Create the table with a UNIQUE composite constraint
    create_table = PostgresOperator(
        task_id='create_table',
        postgres_conn_id=CONN_ID,
        sql="""
            CREATE TABLE IF NOT EXISTS bitcoin_realtime (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10),
                price_usd NUMERIC(18, 2),
                volume_24h NUMERIC(20, 2),
                market_cap NUMERIC(20, 2),
                fetched_at TIMESTAMP,
                CONSTRAINT unique_symbol_fetch_time UNIQUE (symbol, fetched_at)
            );
        """
    )

    # Task 2: Fetch and Store data (enabled with context kwargs)
    store_data = PythonOperator(
        task_id='fetch_and_store_btc',
        python_callable=extract_and_load_data,
        provide_context=True # Tells Airflow to inject execution timelines into **kwargs
    )

    create_table >> store_data