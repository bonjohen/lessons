"""Tests for Azure adapters with mocked Azure SDK clients."""

import sys
from unittest.mock import MagicMock

# Mock Azure SDK modules before importing adapters
mock_openai = MagicMock()
mock_azure_search = MagicMock()
mock_azure_search_indexes = MagicMock()
mock_azure_search_indexes_models = MagicMock()
mock_azure_search_models = MagicMock()
mock_azure_core = MagicMock()
mock_azure_core_credentials = MagicMock()

sys.modules.setdefault("openai", mock_openai)
sys.modules.setdefault("azure", MagicMock())
sys.modules.setdefault("azure.core", mock_azure_core)
sys.modules.setdefault("azure.core.credentials", mock_azure_core_credentials)
sys.modules.setdefault("azure.search", MagicMock())
sys.modules.setdefault("azure.search.documents", mock_azure_search)
sys.modules.setdefault("azure.search.documents.indexes", mock_azure_search_indexes)
sys.modules.setdefault("azure.search.documents.indexes.models", mock_azure_search_indexes_models)
sys.modules.setdefault("azure.search.documents.models", mock_azure_search_models)

from app.adapters.llm.azure_openai_adapter import AzureOpenAIAdapter  # noqa: E402
from app.adapters.vector.azure_search_adapter import AzureSearchAdapter  # noqa: E402


class TestAzureOpenAIAdapter:
    """Tests for AzureOpenAIAdapter with mocked openai client."""

    def _make_adapter(self, mock_client):
        """Create adapter with mocked client."""
        mock_openai.AzureOpenAI.return_value = mock_client
        return AzureOpenAIAdapter(
            endpoint="https://test.openai.azure.com",
            api_key="test-key",
        )

    def test_embed_texts(self):
        mock_client = MagicMock()
        embedding = [0.1] * 768
        mock_item = MagicMock()
        mock_item.embedding = embedding
        mock_response = MagicMock()
        mock_response.data = [mock_item, mock_item]
        mock_client.embeddings.create.return_value = mock_response

        adapter = self._make_adapter(mock_client)
        result = adapter.embed(["hello", "world"])

        assert len(result) == 2
        assert result[0] == embedding
        mock_client.embeddings.create.assert_called_once()

    def test_chat(self):
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "The answer is 42."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        adapter = self._make_adapter(mock_client)
        result = adapter.chat([{"role": "user", "content": "What is the answer?"}])

        assert result == "The answer is 42."

    def test_custom_deployments(self):
        mock_client = MagicMock()
        mock_openai.AzureOpenAI.return_value = mock_client

        adapter = AzureOpenAIAdapter(
            endpoint="https://test.openai.azure.com",
            api_key="test-key",
            embed_deployment="custom-embed",
            chat_deployment="custom-chat",
        )

        assert adapter._embed_deployment == "custom-embed"
        assert adapter._chat_deployment == "custom-chat"


class TestAzureSearchAdapter:
    """Tests for AzureSearchAdapter with mocked Azure SDK."""

    def _make_adapter(self, mock_search_client):
        """Create adapter with mocked clients."""
        mock_azure_search.SearchClient.return_value = mock_search_client
        mock_index_client = MagicMock()
        mock_index_client.get_index.return_value = MagicMock()
        mock_azure_search_indexes.SearchIndexClient.return_value = mock_index_client

        return AzureSearchAdapter(
            endpoint="https://test.search.windows.net",
            api_key="test-key",
        )

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
        mock_client.upload_documents.assert_called_once()

    def test_query(self):
        mock_client = MagicMock()
        mock_result = {
            "chunk_id": "c1",
            "chunk_text": "hello",
            "@search.score": 0.95,
            "lesson_id": "l1",
            "title": "T1",
            "heading_path": "H1",
            "tags": ["a"],
            "lesson_url": "/l/1",
            "repo_id": "r1",
        }
        mock_client.search.return_value = [mock_result]

        adapter = self._make_adapter(mock_client)
        results = adapter.query([0.1] * 768, top_k=5)

        assert len(results) == 1
        assert results[0]["chunk_id"] == "c1"
        assert results[0]["similarity_score"] == 0.95

    def test_count(self):
        mock_client = MagicMock()
        mock_client.get_document_count.return_value = 42
        adapter = self._make_adapter(mock_client)
        assert adapter.count() == 42

    def test_empty_chunks(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)
        count = adapter.index_chunks([], [])
        assert count == 0

    def test_delete_collection(self):
        mock_client = MagicMock()
        adapter = self._make_adapter(mock_client)
        adapter.delete_collection()
        adapter._index_client.delete_index.assert_called_once()
