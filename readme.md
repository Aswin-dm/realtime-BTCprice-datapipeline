realtime-BTCprice-datapipeline

Pulls BTC/crypto price data from the Coinpaprika API on a schedule and writes it into Postgres. Airflow handles the scheduling/retries, Celery + Redis run the tasks across workers, everything runs in Docker.

Calling it "real-time" is a bit generous — it's polling every few minutes, not streaming. More accurate to call it a scheduled ingestion pipeline. The transform step is light too — pulls symbol, price, volume, market cap out of the nested API response into a flat row, nothing aggregated or cleaned yet.

How it works


Airflow DAG (crypto_etl_dag) triggers on a schedule
Extract task hits the Coinpaprika API, gets raw ticker JSON
Transform task flattens it — pulls out symbol, quotes.USD.price, quotes.USD.volume_24h, quotes.USD.market_cap
Load task writes rows into Postgres
If a task fails (API timeout, rate limit, etc.) it retries once after a 1 min delay before giving up


Celery + Redis sit underneath so these tasks can run on separate worker processes instead of all on one Airflow scheduler.

Stack


Apache Airflow — scheduling/orchestration
Celery + Redis — task queue / distributed execution
Python (requests, pandas)
PostgreSQL — storage
Docker / Docker Compose
Coinpaprika API — data source


Running it

Need Docker + Docker Compose installed. Ports 8080 (Airflow), 5432 (Postgres), 6379 (Redis) should be free.

bashgit clone https://github.com/Aswin-dm/realtime-BTCprice-datapipeline.git
cd realtime-BTCprice-datapipeline
cp .env.example .env
docker-compose up -d --build

Then go to http://localhost:8080, log in (default airflow/airflow unless you changed it), and turn on the crypto_etl_dag toggle. It'll start running on its schedule from there.

To check data is actually landing:

bashdocker exec -it <postgres_container> psql -U <user> -d <db> -c "SELECT * FROM <your_table_name> ORDER BY id DESC LIMIT 10;"

docker-compose down to stop everything.

Table

One table right now:


symbol
price
volume (24h)
market_cap


That's it. The diagram in earlier drafts of this had OHLCV/exchange_rates/daily_metrics tables — those don't exist yet, that's more where this could go (see TODO).

TODO


add a timestamp column so this is actually trackable over time, not just latest snapshot
maybe split into OHLCV / historical tables if I want trend data, not just point-in-time
some basic validation before insert (what if the API returns null for a field?)
tests
alerting if the DAG fails
swap polling for something streaming-based if I want this to actually be real-time