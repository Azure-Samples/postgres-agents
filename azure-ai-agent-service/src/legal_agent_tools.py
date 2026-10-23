import pandas as pd
import os
from datetime import datetime
import json
from typing import Any, Callable, Set
from sqlalchemy import create_engine
from azure.ai.projects.telemetry import trace_function
from opentelemetry import trace
from postgres_config import embedding_config, embedding_parameters

CONN_STR = os.getenv("AZURE_PG_CONNECTION")

# The trace_func decorator will trace the function call and enable adding additional attributes
# to the span in the function implementation. Note that this will trace the function parameters and their values.


# Get data from the Postgres database
@trace_function()
def vector_search_cases(
    vector_search_query: str,
    start_date: datetime = "1911-01-01",
    end_date: datetime = "2025-12-31",
    limit: int = 10,
) -> str:
    """
    Fetches the cases information in Washington State for the specified query.

    :param query(str): The query to fetch cases for specifically in Washington.
    :type query: str
    :param start_date: The start date for the search, defaults to "1911-01-01"
    :type start_date: datetime, optional
    :param end_date: The end date for the search, defaults to "2025-12-31"
    :type end_date: datetime, optional
    :param limit: The maximum number of cases to fetch, defaults to 10
    :type limit: int, optional

    :return: Cases information as a JSON string.
    :rtype: str
    """

    db = create_engine(CONN_STR)

    expression, _ = embedding_config()
    query = f"""
    SELECT id, name, opinion, 
    opinions_vector <=> {expression} as similarity
    FROM cases
    WHERE decision_date BETWEEN %s AND %s
    ORDER BY similarity
    LIMIT %s;
    """

    # Fetch cases information from the database
    with db.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params=(
                *embedding_parameters(vector_search_query),
                datetime.strptime(start_date, "%Y-%m-%d"),
                datetime.strptime(end_date, "%Y-%m-%d"),
                limit,
            ),
        )

    # Adding attributes to the current span
    span = trace.get_current_span()
    span.set_attribute("requested_query", query)

    cases_json = json.dumps(df.to_json(orient="records"))
    span.set_attribute("cases_json", cases_json)
    return cases_json


# Count the number of cases related to the specified query
@trace_function()
def count_cases(vector_search_query: str, limit: int = 10) -> str:
    """
    Count the number of cases related to the specified query.
    Invoke this tool for aggregation, if the user mentions the word "count" or "how many" or a similar word.

    :param query(str): The query to search.
    :type query: str
    :param limit: The maximum number of cases fetch, defaults to 10
    :type limit: int, optional

    :return: listing information as a JSON string.
    :rtype: str
    """

    db = create_engine(CONN_STR)

    expression, _ = embedding_config()
    query = f"""
    SELECT COUNT(*) 
    FROM cases
    WHERE opinions_vector <=> {expression} < 0.8
    limit %s;
    """

    with db.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params=(*embedding_parameters(vector_search_query), limit),
        )

    # Adding attributes to the current span
    span = trace.get_current_span()
    span.set_attribute("requested_query", query)
    cases_count = json.dumps(df.to_json(orient="records"))
    span.set_attribute("result", cases_count)

    return cases_count


# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {vector_search_cases, count_cases}
