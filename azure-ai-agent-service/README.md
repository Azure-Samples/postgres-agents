# Build AI Agents with managed PostgreSQL on Azure and Azure AI Agent Service

A legal research assistant that retrieves Washington court cases from **Azure HorizonDB** or **Azure Database for PostgreSQL Flexible Server**.

![Azure AI Agent Service](img/ai_agent_service_and_postgres.png)

## 1. Prepare your services

- Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Azure CLI.
- A **new, empty demo database**, network access, and a PostgreSQL login that can create tables and extensions.
- An Azure AI Foundry **hub-based project**, a deployed chat model, and permission to use the project. This sample pins `azure-ai-projects==1.0.0b7` and uses its project connection string API; a newer endpoint-only project is not interchangeable.

| Database | Embedding setup |
| --- | --- |
| HorizonDB | Use the cluster's **read-write endpoint**. Enable `vector` and `azure_ai` in the demo database. Register or select an embedding model alias that produces **1536 dimensions**, such as `default-embedding`. The loader and search tools call `ai.embed`; they do not configure an external OpenAI key. |
| Flexible Server | Allow `vector` and `azure_ai` in the `azure.extensions` server parameter. Deploy `text-embedding-3-small` in Azure OpenAI and note its **deployment name**, endpoint, and key. The loader configures `azure_ai` and calls `azure_openai.create_embeddings`. |

HorizonDB's registered model must be available in the database you create; do not assume a model registered in another database is inherited. The loader creates the extensions if needed.

## 2. Install and configure

From the repository root:

```bash
cd azure-ai-agent-service
uv sync
cp .env-sample .env
az login
```

Edit `.env`:

| Variable | Value |
| --- | --- |
| `POSTGRES_SERVICE` | `horizondb` or `flex` |
| `AZURE_PG_CONNECTION` | `postgresql://USER:PASSWORD@HOST:5432/agentdb?sslmode=require` |
| `EMBEDDING_MODEL_NAME` | HorizonDB registered alias, or Flex Azure OpenAI embedding deployment name |
| `PROJECT_CONNECTION_STRING` | Connection string from your hub-based Foundry project |
| `MODEL_DEPLOYMENT_NAME` | Chat deployment in that project |
| `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY` | Required for Flex embeddings only |

URL-encode special characters in connection-string credentials. Keep `.env` private. The scripts load it relative to the sample directory, independent of your working directory.

## 3. Load data and run

Start small to limit embedding charges:

```bash
uv run python load_data/main.py --limit 20
uv run python src/simple_postgres_and_ai_agent.py
```

The loader creates `cases`, loads the bundled CSV, and generates embeddings. It **fails without overwriting data** if `cases` already exists. Omit `--limit` to load the complete dataset in a fresh demo database. Loading and query embeddings use the same configured model.

For tracing, enable Application Insights on your Foundry project, then run:

```bash
uv run python src/advanced_postgres_and_ai_agent_with_tracing.py
```

Content tracing is off by default; enable it only if you intend to record prompts and tool results.

## Troubleshooting and cleanup

| Symptom | Check |
| --- | --- |
| Cannot connect | Read-write hostname, port, login, firewall/private network, and TLS |
| Extension creation denied | Role privileges; on Flex, also check `azure.extensions` |
| Embedding/model error | Model is available in this database; Flex uses deployment names, not model catalog names |
| Dimension mismatch | Use a 1536-dimensional embedding model for both load and retrieval |
| Foundry project error | Hub-based project connection string, `az login`, and project permissions |

Delete the demo database only when you no longer need its data, and delete any agents/threads created in Foundry. Do not delete the cluster or server.

The [original walkthrough](https://aka.ms/pg-ai-agents-blog) provides additional background.
