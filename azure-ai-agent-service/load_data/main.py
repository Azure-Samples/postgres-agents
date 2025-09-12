import psycopg2
import csv
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Increase the maximum field size limit
csv.field_size_limit(sys.maxsize)

# Fetch the connection string from the environment variable
CONN_STR = os.getenv("AZURE_PG_CONNECTION")

# Fetch the OpenAI settings from environment variables
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# Fetch the Embedding model name from environment variables
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
                                  
# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(CONN_STR)

# Create a cursor object using the connection
cur = conn.cursor()

# Enable the required extensions
def create_extensions(cur):
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("CREATE EXTENSION IF NOT EXISTS azure_ai")
    print("Extensions created successfully")
    conn.commit()

# Setup OpenAI
def create_openai_connection(cur):
    cur.execute(f"SELECT azure_ai.set_setting('azure_openai.endpoint', '{AZURE_OPENAI_ENDPOINT}')")
    cur.execute(f"SELECT azure_ai.set_setting('azure_openai.subscription_key', '{AZURE_OPENAI_API_KEY}')")
    print("OpenAI connection established successfully")
    conn.commit()

# Drop the cases table if it exists
def create_tables(cur):
    cur.execute("DROP TABLE IF EXISTS cases")
    cur.execute("DROP TABLE IF EXISTS temp_cases_data")
    conn.commit()

    # Create the cases table
    cur.execute("""
        CREATE TABLE cases (
            id SERIAL PRIMARY KEY,
            name TEXT,
            decision_date DATE,
            court_id INT,
            opinion TEXT
        )
    """)
    print("Cases table created successfully")
    conn.commit()

    # Create the temp_cases table
    cur.execute("CREATE TABLE temp_cases_data (data jsonb)")
    conn.commit()
    print("Temp cases table created successfully")

# Load data from the CSV file into the temp_cases table
def ingest_data_to_tables(cur):
    with open('cases.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            json_data = row['data']
            #print(json_data)
            cur.execute("INSERT INTO temp_cases_data (data) VALUES (%s)", [json_data])
    conn.commit()
    print("Data loaded into temp_cases_data table successfully")
    
    # Insert data into the cases table
    cur.execute("""
        INSERT INTO cases
        SELECT
            (data#>>'{id}')::int AS id,
            (data#>>'{name_abbreviation}')::text AS name,
            (data#>>'{decision_date}')::date AS decision_date,
            (data#>>'{court,id}')::int AS court_id,
            array_to_string(ARRAY(
                SELECT jsonb_path_query(data, '$.casebody.opinions[*].text')
            ), ', ') AS opinion
        FROM temp_cases_data
    """)
    conn.commit()
    print("Data loaded into cases table successfully")

# Add Embeddings
def add_embeddings(cur):
    print("Adding Embeddings, this will take a while around 3-5 mins...")
    cur.execute("ALTER TABLE cases ADD COLUMN opinions_vector vector(1536)")
    cur.execute(f"""
        UPDATE cases
        SET opinions_vector = azure_openai.create_embeddings(
            '{EMBEDDING_MODEL_NAME}', 
            name || LEFT(opinion, 8000), 
            max_attempts => 5, 
            retry_delay_ms => 500
        )::vector
        WHERE opinions_vector IS NULL
    """)

    # Commit the transaction
    conn.commit()
    print("Embeddings added successfully")

create_extensions(cur)
create_openai_connection(cur)
create_tables(cur)
ingest_data_to_tables(cur)
add_embeddings(cur)

# Close the cursor and connection
cur.close()
conn.close()

print("All Data loaded successfully!")