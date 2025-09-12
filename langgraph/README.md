# Azure PostgreSQL + LangGraph Demo

Short guide to spin up a local dev environment, configure Azure Postgres, and run the notebook showing unified agent state, memory, chat history, and vector retrieval using LangGraph.

## 1. Prerequisites
- Python 3.10+ recommended
- An Azure Database for PostgreSQL Flexible Server (v14+)
- pgvector & pg_diskann extension available
- Azure OpenAI API key
- (Optional) VS Code with Python + Jupyter extensions

## 2. Clone & Enter Project
If you haven't already:
```bash
git clone https://github.com/Azure-Samples/postgres-agents.git
cd langgraph
```

## 3. Create & Activate Virtual Environment using `uv`

This project uses `pyproject.toml` and `uv` to manage virtual environments and dependencies. `uv` will create a `.venv` folder and install packages from `pyproject.toml`.

Install `uv` if you don't have it (recommended via `pipx`):

```bash
# preferred (isolated)
pipx install uv

# or (quick)
python -m pip install --user uv
```

Create and activate the venv:

```bash
# create .venv (uv will create it on sync too)
uv venv

# activate venv (macOS / Linux)
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1
```

## 4. Install Dependencies from `pyproject.toml`

Install everything defined in `pyproject.toml` (default groups = all):

```bash
# sync installs packages into .venv per pyproject.toml
uv sync
```

Install only specific groups (optional):

```bash
# example: install only core groups, skip dev/tools
uv sync --no-group dev --no-group utilities
```

Notes:

- If `pyproject.toml` references a local wheel (e.g. `dist/langchain_azure_postgresql-*.whl`), ensure the file exists or change the reference to an editable path.
- Re-run `uv sync` after editing `pyproject.toml`.

## 5. Configure Environment Variables
Copy the example file and edit secrets:
```bash
cp .env.example .env
```
Edit `.env` and set:
```
AZURE_PG_HOST=your-server.postgres.database.azure.com
AZURE_PG_DB=agentdb
AZURE_PG_USER=agent_user
AZURE_PG_PASSWORD=********
OPENAI_API_KEY=sk-...
# (Optional Azure OpenAI)
# AZURE_OPENAI_ENDPOINT=...
# AZURE_OPENAI_API_KEY=...
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
# AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

## 6. Run the Notebook
**Option A (VS Code):** 
1. Open the folder, 
3. Open `langgraph.ipynb` 
4. Select Python Environment `langgraph-azure-postgres`. This environment would have been created in previous steps through the pyproject.toml. 
5. Run cells.

**Option B (CLI Jupyter):**
```bash
pip install notebook  # if not already
jupyter notebook
```
Open `langgraph.ipynb` in the browser.

## 7. Common Issues
| Symptom | Fix |
|---------|-----|
| SSL error connecting to DB | Ensure `sslmode=require` & correct host name. |
| `vector` type not found | Run the `CREATE EXTENSION vector;` command. |
| Auth failure | Re-check username format (often ends with `@servername`). |
| Slow vector search | Run `ANALYZE documents;` and adjust IVFFLAT `lists`. |
| OpenAI auth error | Confirm key loaded: `echo $OPENAI_API_KEY`. |

## 8. Cleaning Up
Deactivate venv:
```bash
deactivate
```
Remove build artifacts or cache:
```bash
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
```


