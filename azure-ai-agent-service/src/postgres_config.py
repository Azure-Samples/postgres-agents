import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def embedding_config(text_expression: str = "%s") -> tuple[str, str]:
    """Return SQL and model for the selected service; SQL expressions are internal."""
    service = os.getenv("POSTGRES_SERVICE", "flex").lower()
    if service == "horizondb":
        return (
            f"ai.embed(text => {text_expression}, model => %s, dimensions => 1536)::vector",
            os.getenv("EMBEDDING_MODEL_NAME") or "default-embedding",
        )
    if service == "flex":
        return (
            f"azure_openai.create_embeddings(%s, {text_expression}, "
            "max_attempts => 5, retry_delay_ms => 500)::vector",
            os.getenv("EMBEDDING_MODEL_NAME") or "text-embedding-3-small",
        )
    raise ValueError("POSTGRES_SERVICE must be 'horizondb' or 'flex'")


def embedding_parameters(text: str) -> tuple[str, str]:
    _, model = embedding_config()
    if os.getenv("POSTGRES_SERVICE", "flex").lower() == "horizondb":
        return text, model
    return model, text
