"""Tests for OpenAI adapter with mocked openai client."""

import sys
from unittest.mock import MagicMock

# Ensure openai module is available (real or mock) before importing adapter
mock_openai = MagicMock()
sys.modules.setdefault("openai", mock_openai)

# Get a reference to whatever openai module is in sys.modules
_openai_mod = sys.modules["openai"]

from app.adapters.llm.openai_adapter import OpenAIAdapter  # noqa: E402


class TestOpenAIAdapter:
    """Tests for OpenAIAdapter with mocked openai client."""

    def _make_adapter(self, mock_client):
        """Create adapter with mocked client."""
        _original = _openai_mod.OpenAI
        _openai_mod.OpenAI = MagicMock(return_value=mock_client)
        try:
            adapter = OpenAIAdapter(api_key="test-key")
        finally:
            _openai_mod.OpenAI = _original
        return adapter

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

    def test_custom_models(self):
        _original = _openai_mod.OpenAI
        _openai_mod.OpenAI = MagicMock(return_value=MagicMock())
        try:
            adapter = OpenAIAdapter(
                api_key="test-key",
                embed_model="text-embedding-3-large",
                chat_model="gpt-4o",
            )
        finally:
            _openai_mod.OpenAI = _original

        assert adapter._embed_model == "text-embedding-3-large"
        assert adapter._chat_model == "gpt-4o"

    def test_default_models(self):
        _original = _openai_mod.OpenAI
        _openai_mod.OpenAI = MagicMock(return_value=MagicMock())
        try:
            adapter = OpenAIAdapter(api_key="test-key")
        finally:
            _openai_mod.OpenAI = _original

        assert adapter._embed_model == "text-embedding-3-small"
        assert adapter._chat_model == "gpt-4o-mini"
