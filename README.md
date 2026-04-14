Real-time BTC Price Data Pipeline
An end-to-end data engineering pipeline designed to fetch, process, and visualize Bitcoin (BTC) price data in real-time. This project leverages Apache Airflow for orchestration, Docker for containerization, and a Python-based frontend for data visualization.

📌 Project Overview
The pipeline automates the extraction of live Bitcoin price data from a cryptocurrency API, processes it, and stores/logs it for real-time monitoring. The goal is to demonstrate a scalable data ingestion workflow suitable for financial data analysis.

🛠 Tech Stack
Language: Python 3.x

Orchestration: Apache Airflow

Containerization: Docker & Docker Compose

Data Source: Crypto Price API (e.g., CoinGecko or Binance)

Frontend/Visualization: Streamlit / Flask (as found in the frontend directory)

📂 Project Structure
```
realtime-BTCprice-datapipeline/
├── dags/                   # Airflow DAG definitions
├── frontend/               # Dashboard/Visualization code
├── logs/                   # Pipeline execution logs
├── mainfile/               # Core processing scripts
├── docker-compose.yaml     # Docker services configuration
└── README.md               # Project documentation
```
🚀 Getting Started
1. Prerequisites
Ensure you have the following installed:

Docker Desktop

Python 3.9+

2. Installation
Clone the repository:

Bash
```
git clone https://github.com/Aswin-dm/realtime-BTCprice-datapipeline.git
cd realtime-BTCprice-datapipeline
```
3. Setup and Run
Launch the entire stack using Docker Compose:

Bash
```
docker-compose up -d
```
This will spin up the Airflow webserver, scheduler, and the associated database.

4. Accessing the Pipeline
```
Airflow UI: Open http://localhost:8080 to monitor and trigger the DAGs.
```
Frontend Dashboard: Navigate to the frontend directory and check the specific service port (usually http://localhost:8501 if using Streamlit).

⚙️ Pipeline Workflow
Extraction: A Python script in the mainfile or dags folder polls a real-time API for the current BTC price.

Transformation: The data is cleaned and formatted (timestamping, currency conversion).

Logging/Storage: Data is logged in the logs/ directory or sent to a database for persistence.

Visualization: The frontend pulls the latest data points to display a live price chart.
