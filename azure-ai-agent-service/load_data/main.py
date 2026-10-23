import argparse
from contextlib import closing
import csv
import os
from pathlib import Path
import sys

import psycopg2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from postgres_config import embedding_config  # noqa: E402


csv.field_size_limit(sys.maxsize)


def load_cases(limit: int | None = None) -> None:
    expression, model = embedding_config("name || LEFT(opinion, 8000)")
    service = os.getenv("POSTGRES_SERVICE", "flex").lower()
    with closing(psycopg2.connect(os.environ["AZURE_PG_CONNECTION"])) as conn, conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("CREATE EXTENSION IF NOT EXISTS azure_ai")
            if service == "flex":
                for setting, variable in (
                    ("azure_openai.endpoint", "AZURE_OPENAI_ENDPOINT"),
                    ("azure_openai.subscription_key", "AZURE_OPENAI_API_KEY"),
                ):
                    cur.execute(
                        "SELECT azure_ai.set_setting(%s, %s)",
                        (setting, os.environ[variable]),
                    )

            # Fail rather than overwrite an existing demo or application table.
            cur.execute("""
                CREATE TABLE cases (
                    id INT PRIMARY KEY,
                    name TEXT,
                    decision_date DATE,
                    court_id INT,
                    opinion TEXT,
                    opinions_vector vector(1536)
                )
            """)
            cur.execute("CREATE TEMP TABLE temp_cases_data (data jsonb) ON COMMIT DROP")
            with Path(__file__).with_name("cases.csv").open(newline="") as source:
                for index, row in enumerate(csv.DictReader(source)):
                    if limit is not None and index >= limit:
                        break
                    cur.execute(
                        "INSERT INTO temp_cases_data (data) VALUES (%s)", (row["data"],)
                    )
            cur.execute("""
                INSERT INTO cases (id, name, decision_date, court_id, opinion)
                SELECT
                    (data#>>'{id}')::int,
                    data#>>'{name_abbreviation}',
                    (data#>>'{decision_date}')::date,
                    (data#>>'{court,id}')::int,
                    array_to_string(ARRAY(
                        SELECT jsonb_path_query(data, '$.casebody.opinions[*].text')
                    ), ', ')
                FROM temp_cases_data
            """)
            print("Generating 1536-dimensional embeddings...")
            cur.execute(
                f"UPDATE cases SET opinions_vector = {expression} "
                "WHERE opinions_vector IS NULL",
                (model,),
            )
            loaded_count = cur.rowcount
    print(f"Loaded and embedded {loaded_count} cases.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load legal cases into a new demo database."
    )
    parser.add_argument("--limit", type=int, help="Load only the first N cases.")
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    load_cases(args.limit)


if __name__ == "__main__":
    main()
