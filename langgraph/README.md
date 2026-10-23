# LangGraph with managed PostgreSQL on Azure

Use **Azure HorizonDB** or **Azure Database for PostgreSQL Flexible Server** as one store for vector retrieval, agent checkpoints, conversation history, and long-term memory.

## 1. Prepare your services

- Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and VS Code with Python and Jupyter extensions.
- A **new demo database**, PostgreSQL login, and network access from your machine.
- Azure OpenAI embedding and chat deployments. This notebook calls Azure OpenAI from Python on **both** database services; a HorizonDB managed-model registration is not required.

| Database | Setup |
| --- | --- |
| HorizonDB | Copy the cluster's **read-write endpoint**, port, and login from its connection details. |
| Flexible Server | Copy the server's connection details and allow `vector` and `pg_diskann` in `azure.extensions`. |

The notebook creates `vector` and `pg_diskann`, so your role needs permission to create these extensions and the demo tables.

## 2. Install and configure

From the repository root:

```bash
cd langgraph
uv sync
cp .env.example .env
```

Edit `.env` with your database's `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`. Keep `PGSSLMODE=require`.

For Azure OpenAI, set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT` (chat), and `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`. Use your **deployment names**. Alternatively, set `OPENAI_API_KEY` and remove the Azure OpenAI key to use OpenAI.

Keep `.env` private. Tracing is disabled by default.

## 3. Run the notebook

Open `langgraph.ipynb` in VS Code, select `langgraph/.venv/bin/python` (Windows: `.venv\Scripts\python.exe`) as the kernel, and **Run All**.

The notebook selects password authentication when `PGPASSWORD` is set. To use Microsoft Entra authentication instead, remove `PGPASSWORD`, run `az login`, and set `PGUSER` to your database's provisioned Entra role. The database must already be configured for that identity.

Cells demonstrate vector insert/search/update/delete, filtered retrieval, checkpointed conversations, long-term memory, and a retrieval agent. They create persistent tables in the demo database and call paid model APIs.

## Troubleshooting and cleanup

| Symptom | Check |
| --- | --- |
| Connection or TLS error | Actual read-write endpoint, port, `PGSSLMODE`, and network access |
| Authentication failure | Database login; for Entra, database role provisioning and `az login` |
| Missing extension | Creation privileges; Flex extension allowlist |
| Azure OpenAI error | Endpoint, API version, deployment names, and key |
| Unexpected old conversation | Use a new thread ID or a fresh demo database |

Run the final cleanup cell to release pooled connections. Delete the dedicated demo database when finished; do not delete the cluster or server.
