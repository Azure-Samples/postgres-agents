# Build AI Agents with managed PostgreSQL on Azure

Build agents with **Azure HorizonDB** or **Azure Database for PostgreSQL Flexible Server** using PostgreSQL for vector retrieval, conversation history, and agent state.

## Choose a sample

| Sample | What you build | Start here |
| --- | --- | --- |
| LangGraph + LangChain | An agent with vector search, checkpoints, and long-term memory | [Quickstart](./langgraph/) |
| Azure AI Agent Service | A legal research assistant with PostgreSQL search tools | [Quickstart](./azure-ai-agent-service/) |

Both samples connect over PostgreSQL with TLS. Use a **new demo database**, not a database containing production data.

## Choose your database

| Service | Database setup |
| --- | --- |
| Azure HorizonDB | Copy the **read-write endpoint**, port, and username from your cluster's connection details. The legal-agent sample uses a registered HorizonDB embedding model; LangGraph uses Azure OpenAI from the client. |
| Azure Database for PostgreSQL Flexible Server | Copy your server's connection details. Allow the extensions used by your sample in the `azure.extensions` server parameter before running it. |

Allow network access from your development machine and use a role that can create the sample tables and extensions. Follow the selected quickstart for environment variables and run commands.
