"""Tests for query result caching in retriever and generator."""

from unittest.mock import MagicMock

from app.rag.generator import Generator
from app.rag.retriever import Retriever


class TestGeneratorCaching:
    def test_second_call_skips_llm(self):
        mock_llm = MagicMock()
        mock_vector = MagicMock()

        mock_llm.embed.return_value = [[0.1, 0.2]]
        mock_vector.query.return_value = [
            {
                "chunk_id": "c1",
                "chunk_text": "text",
                "similarity_score": 0.9,
                "lesson_id": "l1",
                "title": "T",
                "heading_path": "H",
                "lesson_url": "/l/l1",
                "repo_id": "r1",
            },
        ]
        mock_llm.chat.return_value = "Answer text"

        retriever = Retriever(vector=mock_vector, llm=mock_llm)
        generator = Generator(retriever=retriever, llm=mock_llm)

        result1 = generator.generate("test query")
        result2 = generator.generate("test query")

        assert result1 == result2
        assert mock_llm.chat.call_count == 1

    def test_different_queries_not_cached(self):
        mock_llm = MagicMock()
        mock_vector = MagicMock()

        mock_llm.embed.return_value = [[0.1, 0.2]]
        mock_vector.query.return_value = [
            {
                "chunk_id": "c1",
                "chunk_text": "text",
                "similarity_score": 0.9,
                "lesson_id": "l1",
                "title": "T",
                "heading_path": "H",
                "lesson_url": "/l/l1",
                "repo_id": "r1",
            },
        ]
        mock_llm.chat.return_value = "Answer"

        retriever = Retriever(vector=mock_vector, llm=mock_llm)
        generator = Generator(retriever=retriever, llm=mock_llm)

        generator.generate("query A")
        generator.generate("query B")

        assert mock_llm.chat.call_count == 2


class TestRetrieverCaching:
    def test_second_call_skips_embed(self):
        mock_llm = MagicMock()
        mock_vector = MagicMock()

        mock_llm.embed.return_value = [[0.1, 0.2]]
        mock_vector.query.return_value = [{"chunk_id": "c1", "chunk_text": "t"}]

        retriever = Retriever(vector=mock_vector, llm=mock_llm)

        r1 = retriever.retrieve("same query")
        r2 = retriever.retrieve("same query")

        assert r1 == r2
        assert mock_llm.embed.call_count == 1
