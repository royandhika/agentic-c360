import os
from dotenv import load_dotenv
import clickhouse_connect

load_dotenv()

def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DB", "wanderfuel"),
    )
