import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

SAMPLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SAMPLE / "src"))
sys.path.insert(0, str(SAMPLE / "load_data"))

import main as loader  # noqa: E402
import legal_agent_tools  # noqa: E402
from postgres_config import embedding_config, embedding_parameters  # noqa: E402


class PostgresSupportTests(unittest.TestCase):
    def test_embedding_sql_and_parameter_order(self):
        for service, function, expected in (
            ("horizondb", "ai.embed", ("a query's text", "custom-model")),
            (
                "flex",
                "azure_openai.create_embeddings",
                ("custom-model", "a query's text"),
            ),
        ):
            with (
                self.subTest(service=service),
                patch.dict(
                    os.environ,
                    {
                        "POSTGRES_SERVICE": service,
                        "EMBEDDING_MODEL_NAME": "custom-model",
                    },
                ),
            ):
                expression, model = embedding_config()
                self.assertIn(function, expression)
                self.assertNotIn("custom-model", expression)
                self.assertEqual(model, "custom-model")
                self.assertEqual(embedding_parameters("a query's text"), expected)

    def test_defaults_preserve_flex_and_select_horizon_alias(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                embedding_parameters("query"), ("text-embedding-3-small", "query")
            )
            os.environ["POSTGRES_SERVICE"] = "horizondb"
            self.assertEqual(
                embedding_parameters("query"), ("query", "default-embedding")
            )

    def test_unknown_service_fails_explicitly(self):
        with patch.dict(os.environ, {"POSTGRES_SERVICE": "typo"}):
            with self.assertRaisesRegex(ValueError, "POSTGRES_SERVICE"):
                embedding_config()

    def test_loader_routes_embeddings_and_configures_only_flex(self):
        for service, function in (
            ("horizondb", "ai.embed"),
            ("flex", "azure_openai.create_embeddings"),
        ):
            with (
                self.subTest(service=service),
                patch.dict(
                    os.environ,
                    {
                        "POSTGRES_SERVICE": service,
                        "EMBEDDING_MODEL_NAME": "deployment's name",
                        "AZURE_PG_CONNECTION": "test-connection",
                        "AZURE_OPENAI_ENDPOINT": "https://example.invalid",
                        "AZURE_OPENAI_API_KEY": "placeholder",
                    },
                ),
                patch.object(loader.psycopg2, "connect") as connect,
            ):
                cursor = connect.return_value.cursor.return_value.__enter__.return_value
                cursor.rowcount = 2
                loader.load_cases(limit=2)
                calls = cursor.execute.call_args_list
                inserts = [
                    c
                    for c in calls
                    if c.args[0].startswith("INSERT INTO temp_cases_data")
                ]
                self.assertEqual(len(inserts), 2)
                updates = [c for c in calls if c.args[0].startswith("UPDATE cases")]
                self.assertEqual(len(updates), 1)
                self.assertIn(function, updates[0].args[0])
                self.assertEqual(updates[0].args[1], ("deployment's name",))
                settings = [c for c in calls if "azure_ai.set_setting" in c.args[0]]
                self.assertEqual(len(settings), 2 if service == "flex" else 0)
                self.assertFalse(any("DROP TABLE" in c.args[0] for c in calls))
                connect.return_value.close.assert_called_once()

    def test_existing_cases_table_aborts_without_loading_data(self):
        with (
            patch.dict(
                os.environ,
                {
                    "POSTGRES_SERVICE": "horizondb",
                    "AZURE_PG_CONNECTION": "test-connection",
                },
            ),
            patch.object(loader.psycopg2, "connect") as connect,
        ):
            cursor = connect.return_value.cursor.return_value.__enter__.return_value

            def execute(statement, *parameters):
                if "CREATE TABLE cases" in statement:
                    raise loader.psycopg2.errors.DuplicateTable("cases already exists")

            cursor.execute.side_effect = execute
            with self.assertRaises(loader.psycopg2.errors.DuplicateTable):
                loader.load_cases(limit=2)
            self.assertFalse(
                any(
                    "INSERT INTO" in call.args[0]
                    for call in cursor.execute.call_args_list
                )
            )
            connect.return_value.close.assert_called_once()

    def test_search_tools_use_the_same_model_and_service_as_loader(self):
        for service, function in (
            ("horizondb", "ai.embed"),
            ("flex", "azure_openai.create_embeddings"),
        ):
            with (
                self.subTest(service=service),
                patch.dict(
                    os.environ,
                    {
                        "POSTGRES_SERVICE": service,
                        "EMBEDDING_MODEL_NAME": "custom-model",
                    },
                ),
                patch.object(legal_agent_tools, "create_engine"),
                patch.object(legal_agent_tools.pd, "read_sql") as read_sql,
            ):
                frame = MagicMock()
                frame.to_json.return_value = '[{"id": 1}]'
                read_sql.return_value = frame
                legal_agent_tools.vector_search_cases("query's text")
                legal_agent_tools.count_cases("query's text")
                for call in read_sql.call_args_list:
                    self.assertIn(function, call.args[0])
                    self.assertNotIn("query's text", call.args[0])
                    self.assertEqual(
                        call.kwargs["params"][:2],
                        embedding_parameters("query's text"),
                    )


if __name__ == "__main__":
    unittest.main()
