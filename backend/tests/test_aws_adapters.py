"""Tests for AWS adapters with mocked boto3 clients."""

import io
import json
import sys
from unittest.mock import MagicMock

# Create mock modules for boto3 and opensearch before importing adapters
mock_boto3 = MagicMock()
mock_opensearchpy = MagicMock()
mock_aws4auth = MagicMock()

sys.modules.setdefault("boto3", mock_boto3)
sys.modules.setdefault("opensearchpy", mock_opensearchpy)
sys.modules.setdefault("requests_aws4auth", mock_aws4auth)

from app.adapters.llm.bedrock_adapter import BedrockAdapter  # noqa: E402
from app.adapters.vector.opensearch_adapter import OpenSearchAdapter  # noqa: E402


class TestBedrockAdapter:
    """Tests for BedrockAdapter with mocked boto3."""

    def _make_adapter(self, mock_client):
        """Create a BedrockAdapter with a mocked boto3 client."""
        mock_boto3.client.return_value = mock_client
        return BedrockAdapter()

    def test_embed_single_text(self):
        mock_client = MagicMock()
        embedding = [0.1] * 768
        response_body = json.dumps({"embedding": embedding})
        mock_client.invoke_model.return_value = {"body": io.BytesIO(response_body.encode())}

        adapter = self._make_adapter(mock_client)
        result = adapter.embed(["hello world"])

        assert len(result) == 1
        assert result[0] == embedding
        mock_client.invoke_model.assert_called_once()

    def test_embed_multiple_texts(self):
        mock_client = MagicMock()
        embedding = [0.5] * 768
        response_body = json.dumps({"embedding": embedding})
        mock_client.invoke_model.side_effect = [
            {"body": io.BytesIO(response_body.encode())},
            {"body": io.BytesIO(response_body.encode())},
            {"body": io.BytesIO(response_body.encode())},
        ]

        adapter = self._make_adapter(mock_client)
        result = adapter.embed(["a", "b", "c"])

        assert len(result) == 3
        assert mock_client.invoke_model.call_count == 3

    def test_chat_with_system_message(self):
        mock_client = MagicMock()
        response_body = json.dumps({"content": [{"text": "The answer is 42."}]})
        mock_client.invoke_model.return_value = {"body": io.BytesIO(response_body.encode())}

        adapter = self._make_adapter(mock_client)
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is the answer?"},
        ]
        result = adapter.chat(messages)

        assert result == "The answer is 42."
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert body["system"] == "You are helpful."
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"

    def test_chat_without_system_message(self):
        mock_client = MagicMock()
        response_body = json.dumps({"content": [{"text": "Hello!"}]})
        mock_client.invoke_model.return_value = {"body": io.BytesIO(response_body.encode())}

        adapter = self._make_adapter(mock_client)
        result = adapter.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello!"
        call_args = mock_client.invoke_model.call_args
        body = json.loads(call_args.kwargs["body"])
        assert "system" not in body

    def test_custom_model_ids(self):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        adapter = BedrockAdapter(
            embed_model="custom-embed",
            chat_model="custom-chat",
            region="us-west-2",
        )

        assert adapter._embed_model == "custom-embed"
        assert adapter._chat_model == "custom-chat"
        mock_boto3.client.assert_called_with("bedrock-runtime", region_name="us-west-2")


class TestOpenSearchAdapter:
    """Tests for OpenSearchAdapter with mocked opensearch-py."""

    def _make_adapter(self, mock_os_client):
        """Create an OpenSearchAdapter with mocked clients."""
        mock_opensearchpy.OpenSearch.return_value = mock_os_client
        mock_os_client.indices.exists.return_value = True
        mock_session = MagicMock()
        mock_creds = MagicMock()
        mock_creds.access_key = "test"
        mock_creds.secret_key = "test"
        mock_creds.token = "test"
        mock_session.get_credentials.return_value = mock_creds
        mock_boto3.Session.return_value = mock_session
        return OpenSearchAdapter(endpoint="test.opensearch.aws", region="us-east-1")

    def test_index_chunks(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)

        chunks = [
            {
                "chunk_id": "c1",
                "chunk_text": "hello",
                "lesson_id": "l1",
                "repo_id": "r1",
                "title": "T1",
                "summary": "S1",
                "heading_path": "H1",
                "lesson_url": "/l/1",
                "tags": ["a"],
                "chunk_index": 0,
            }
        ]
        embeddings = [[0.1] * 768]

        count = adapter.index_chunks(chunks, embeddings)
        assert count == 1
        mock_client.index.assert_called_once()

    def test_query(self):
        mock_client = MagicMock()
        mock_client.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_score": 0.95,
                        "_source": {
                            "chunk_id": "c1",
                            "chunk_text": "hello",
                            "lesson_id": "l1",
                            "title": "T1",
                            "heading_path": "H1",
                            "tags": ["a"],
                            "lesson_url": "/l/1",
                            "repo_id": "r1",
                        },
                    }
                ]
            }
        }

        adapter = self._make_adapter(mock_client)
        results = adapter.query([0.1] * 768, top_k=5)

        assert len(results) == 1
        assert results[0]["chunk_id"] == "c1"
        assert results[0]["similarity_score"] == 0.95

    def test_delete_collection(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)
        # Reset exists mock to return True for delete, then False+True for recreate
        mock_client.indices.exists.side_effect = [True, False]
        adapter.delete_collection()
        mock_client.indices.delete.assert_called_once()

    def test_count(self):
        mock_client = MagicMock()
        mock_client.count.return_value = {"count": 42}
        adapter = self._make_adapter(mock_client)
        assert adapter.count() == 42

    def test_empty_chunks(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)
        count = adapter.index_chunks([], [])
        assert count == 0

    def test_creates_index_if_missing(self):
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = False
        mock_opensearchpy.OpenSearch.return_value = mock_client
        mock_session = MagicMock()
        mock_creds = MagicMock()
        mock_creds.access_key = "test"
        mock_creds.secret_key = "test"
        mock_creds.token = "test"
        mock_session.get_credentials.return_value = mock_creds
        mock_boto3.Session.return_value = mock_session

        OpenSearchAdapter(endpoint="test.opensearch.aws", region="us-east-1")

        mock_client.indices.create.assert_called_once()
