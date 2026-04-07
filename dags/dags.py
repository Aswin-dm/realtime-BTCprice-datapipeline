from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from datetime import timedelta
import requests
import logging

# --- CONFIGURATION ---
CONN_ID = '**'  # Must match the ID you just created
COIN_ID = '**'
API_URL = f"https://{COIN_ID}"

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

def extract_and_load_data(**kwargs):
    """
    Fetches data from Coinpaprika and inserts it into Postgres using the Hook.
    """
    # 1. EXTRACT (Get data from API)
    logging.info(f"Fetching data for {COIN_ID}...")
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    # 2. TRANSFORM (Select only what we need)
    symbol = data['symbol']
    price = data['quotes']['USD']['price']
    volume = data['quotes']['USD']['volume_24h']
    market_cap = data['quotes']['USD']['market_cap']

    logging.info(f"Price: ${price}, Volume: {volume}")

    # 3. LOAD (Insert into DB)
    # The Hook handles the connection using your 'crypto_db' credentials
    pg_hook = PostgresHook(postgres_conn_id=CONN_ID)
    
    insert_sql = """
        INSERT INTO bitcoin_realtime (symbol, price_usd, volume_24h, market_cap, fetched_at)
        VALUES (%s, %s, %s, %s, NOW());
    """
    
    pg_hook.run(insert_sql, parameters=(symbol, price, volume, market_cap))
    logging.info("Data successfully inserted into Postgres!")

with DAG(
    dag_id="05_bitcoin_pipeline",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="@hourly", 
    catchup=False,
    tags=['crypto']
) as dag:

    # Task 1: Create the table first
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
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    )

    # Task 2: Fetch and Store data
    store_data = PythonOperator(
        task_id='fetch_and_store_btc',
        python_callable=extract_and_load_data
    )

    # Set dependency: Table must exist before we store data
    create_table >> store_data
