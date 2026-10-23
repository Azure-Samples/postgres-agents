import json
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from psycopg.conninfo import conninfo_to_dict


CELLS = {
    cell["id"]: "".join(cell["source"])
    for cell in json.loads(Path(__file__).with_name("langgraph.ipynb").read_text())[
        "cells"
    ]
}


class NotebookConfigurationTests(unittest.TestCase):
    def test_password_connection_uses_all_database_settings(self):
        for host in (
            "cluster.rw.example.horizondb.azure.com",
            "server.postgres.database.azure.com",
        ):
            pool = MagicMock()
            with (
                self.subTest(host=host),
                patch.dict(
                    os.environ,
                    {
                        "PGHOST": host,
                        "PGDATABASE": "agentdb",
                        "PGUSER": "demo user",
                        "PGPASSWORD": "password with ' and @",
                        "PGPORT": "6432",
                        "PGSSLMODE": "verify-full",
                    },
                    clear=True,
                ),
            ):
                scope = {
                    "os": os,
                    "ConnectionPool": pool,
                    "configure_connection": MagicMock(),
                    "DefaultAzureCredential": MagicMock(),
                    "Connection": MagicMock(),
                    "create_extensions": MagicMock(),
                    "Extension": MagicMock(),
                }
                exec(CELLS["99b51889"], scope)
                options = conninfo_to_dict(pool.call_args.kwargs["conninfo"]())
                self.assertEqual(options["host"], host)
                self.assertEqual(options["user"], "demo user")
                self.assertEqual(options["password"], "password with ' and @")
                self.assertEqual(options["port"], "6432")
                self.assertEqual(options["sslmode"], "verify-full")
                scope["DefaultAzureCredential"].assert_not_called()
                pool.return_value.wait.assert_called_once()

    def test_entra_connection_uses_explicit_role_and_fresh_token(self):
        pool = MagicMock()
        credential = MagicMock()
        credential.get_token.return_value.token = "first-token"
        with patch.dict(
            os.environ,
            {
                "PGHOST": "cluster.rw.example.horizondb.azure.com",
                "PGDATABASE": "agentdb",
                "PGUSER": "entra-role",
            },
            clear=True,
        ):
            scope = {
                "os": os,
                "ConnectionPool": pool,
                "configure_connection": MagicMock(),
                "DefaultAzureCredential": MagicMock(return_value=credential),
                "Connection": MagicMock(),
                "create_extensions": MagicMock(),
                "Extension": MagicMock(),
            }
            exec(CELLS["99b51889"], scope)
            factory = pool.call_args.kwargs["conninfo"]
            self.assertEqual(conninfo_to_dict(factory())["user"], "entra-role")
            self.assertEqual(conninfo_to_dict(factory())["password"], "first-token")
            credential.get_token.return_value.token = "refreshed-token"
            self.assertEqual(conninfo_to_dict(factory())["password"], "refreshed-token")

    def test_azure_models_use_configured_deployment_names(self):
        with (
            patch.dict(
                os.environ,
                {
                    "AZURE_OPENAI_API_KEY": "placeholder",
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "custom-embedding",
                    "AZURE_OPENAI_DEPLOYMENT": "custom-chat",
                    "AZURE_OPENAI_API_VERSION": "2024-10-21",
                },
                clear=True,
            ),
            patch("langchain_openai.AzureOpenAIEmbeddings") as embeddings,
            patch("langchain_openai.AzureChatOpenAI") as chat,
        ):
            exec(CELLS["1b6cbc72"], {"os": os})
            embeddings.assert_called_once_with(
                azure_deployment="custom-embedding",
                api_version="2024-10-21",
            )
            chat.assert_called_once_with(
                azure_deployment="custom-chat",
                api_version="2024-10-21",
            )


if __name__ == "__main__":
    unittest.main()
