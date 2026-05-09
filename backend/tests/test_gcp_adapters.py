"""Tests for GCP adapters with mocked Google Cloud SDK clients."""

import sys
from unittest.mock import MagicMock

# Mock Google Cloud SDK modules before importing adapters
mock_vertexai = MagicMock()
mock_vertexai_language = MagicMock()
mock_vertexai_generative = MagicMock()
mock_google_cloud = MagicMock()
mock_google_cloud_aiplatform = MagicMock()

sys.modules.setdefault("vertexai", mock_vertexai)
sys.modules.setdefault("vertexai.language_models", mock_vertexai_language)
sys.modules.setdefault("vertexai.generative_models", mock_vertexai_generative)
sys.modules.setdefault("google", MagicMock())
sys.modules.setdefault("google.cloud", mock_google_cloud)
sys.modules.setdefault("google.cloud.aiplatform", mock_google_cloud_aiplatform)

from app.adapters.llm.vertex_adapter import VertexAIAdapter  # noqa: E402
from app.adapters.vector.vertex_adapter import VertexVectorSearchAdapter  # noqa: E402


class TestVertexAIAdapter:
    """Tests for VertexAIAdapter with mocked Vertex AI SDK."""

    def _make_adapter(self):
        """Create adapter with mocked models."""
        mock_embed_model = MagicMock()
        mock_chat_model = MagicMock()
        mock_vertexai_language.TextEmbeddingModel.from_pretrained.return_value = mock_embed_model
        mock_vertexai_generative.GenerativeModel.return_value = mock_chat_model
        adapter = VertexAIAdapter(project="test-project", location="us-central1")
        return adapter, mock_embed_model, mock_chat_model

    def test_embed_texts(self):
        adapter, mock_embed, _ = self._make_adapter()
        mock_e1 = MagicMock()
        mock_e1.values = [0.1] * 768
        mock_e2 = MagicMock()
        mock_e2.values = [0.2] * 768
        mock_embed.get_embeddings.return_value = [mock_e1, mock_e2]

        result = adapter.embed(["hello", "world"])

        assert len(result) == 2
        assert result[0] == [0.1] * 768
        mock_embed.get_embeddings.assert_called_once_with(["hello", "world"])

    def test_chat(self):
        adapter, _, mock_chat = self._make_adapter()
        mock_response = MagicMock()
        mock_response.text = "The answer is 42."
        mock_chat.generate_content.return_value = mock_response

        result = adapter.chat(
            [
                {"role": "system", "content": "Be helpful."},
                {"role": "user", "content": "What is the answer?"},
            ]
        )

        assert result == "The answer is 42."
        mock_chat.generate_content.assert_called_once()

    def test_chat_without_system(self):
        adapter, _, mock_chat = self._make_adapter()
        mock_response = MagicMock()
        mock_response.text = "Hello!"
        mock_chat.generate_content.return_value = mock_response

        result = adapter.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello!"
        call_args = mock_chat.generate_content.call_args[0][0]
        assert "System:" not in call_args


class TestVertexVectorSearchAdapter:
    """Tests for VertexVectorSearchAdapter with mocked aiplatform."""

    def _make_adapter(self):
        """Create adapter with mocked aiplatform."""
        adapter = VertexVectorSearchAdapter(
            project="test-project",
            location="us-central1",
            index_id="",
            index_endpoint_id="",
        )
        return adapter

    def test_index_chunks(self):
        adapter = self._make_adapter()
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
        count = adapter.index_chunks(chunks, [[0.1] * 768])
        assert count == 1
        assert "c1" in adapter._chunks_store

    def test_empty_chunks(self):
        adapter = self._make_adapter()
        assert adapter.index_chunks([], []) == 0

    def test_count(self):
        adapter = self._make_adapter()
        assert adapter.count() == 0
        adapter._chunks_store["c1"] = {"chunk_text": "hi"}
        assert adapter.count() == 1

    def test_delete_collection(self):
        adapter = self._make_adapter()
        adapter._chunks_store["c1"] = {"chunk_text": "hi"}
        adapter.delete_collection()
        assert adapter.count() == 0

    def test_query_no_endpoint(self):
        adapter = self._make_adapter()
        results = adapter.query([0.1] * 768)
        assert results == []
