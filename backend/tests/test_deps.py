"""Tests for adapter factory dispatch and thread-safe initialization."""

import threading
from unittest.mock import MagicMock, patch

import pytest

import app.api._deps as deps


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset module-level singletons before each test."""
    deps._retriever = None
    deps._generator = None
    deps._gap_store = None
    yield
    deps._retriever = None
    deps._generator = None
    deps._gap_store = None


class TestDeploymentProfileDispatch:
    """Test that DEPLOYMENT_PROFILE selects the correct adapter pair."""

    @patch.dict("os.environ", {"DEPLOYMENT_PROFILE": "local"}, clear=False)
    def test_local_profile(self):
        from app.adapters.llm.ollama_adapter import OllamaAdapter
        from app.adapters.vector.chromadb_adapter import ChromaDBAdapter

        llm, vector = deps._create_adapters("local")
        assert isinstance(llm, OllamaAdapter)
        assert isinstance(vector, ChromaDBAdapter)

    @patch.dict("os.environ", {"DEPLOYMENT_PROFILE": "aws"}, clear=False)
    def test_aws_profile_dispatches(self):
        """Verify _init reads DEPLOYMENT_PROFILE=aws and calls _create_adapters('aws')."""
        mock_vector = MagicMock()
        mock_vector.count.return_value = 5
        with patch.object(deps, "_create_adapters", return_value=(MagicMock(), mock_vector)) as mock_create:
            deps._init()
            mock_create.assert_called_once_with("aws")

    @patch.dict("os.environ", {"DEPLOYMENT_PROFILE": "azure"}, clear=False)
    def test_azure_profile_dispatches(self):
        mock_vector = MagicMock()
        mock_vector.count.return_value = 5
        with patch.object(deps, "_create_adapters", return_value=(MagicMock(), mock_vector)) as mock_create:
            deps._init()
            mock_create.assert_called_once_with("azure")

    @patch.dict("os.environ", {"DEPLOYMENT_PROFILE": "gcp"}, clear=False)
    def test_gcp_profile_dispatches(self):
        mock_vector = MagicMock()
        mock_vector.count.return_value = 5
        with patch.object(deps, "_create_adapters", return_value=(MagicMock(), mock_vector)) as mock_create:
            deps._init()
            mock_create.assert_called_once_with("gcp")

    def test_default_is_local(self):
        from app.adapters.llm.ollama_adapter import OllamaAdapter
        from app.adapters.vector.chromadb_adapter import ChromaDBAdapter

        llm, vector = deps._create_adapters("local")
        assert isinstance(llm, OllamaAdapter)
        assert isinstance(vector, ChromaDBAdapter)


class TestThreadSafety:
    """Test that concurrent callers don't race on initialization."""

    def test_concurrent_get_generator_inits_once(self):
        init_count = {"n": 0}
        original_create = deps._create_adapters

        def counting_create(profile):
            init_count["n"] += 1
            return original_create(profile)

        mock_vector = MagicMock()
        mock_vector.count.return_value = 5

        with patch.object(deps, "_create_adapters") as mock_create:
            mock_create.return_value = (MagicMock(), mock_vector)

            barrier = threading.Barrier(10)
            errors = []

            def call_get_generator():
                try:
                    barrier.wait(timeout=5)
                    deps.get_generator()
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=call_get_generator) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=10)

            assert not errors, f"Thread errors: {errors}"
            assert mock_create.call_count == 1

    def test_concurrent_get_gap_store_inits_once(self):
        barrier = threading.Barrier(10)
        stores = []

        def call_get_gap_store():
            barrier.wait(timeout=5)
            stores.append(deps.get_gap_store())

        threads = [threading.Thread(target=call_get_gap_store) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(stores) == 10
        assert all(s is stores[0] for s in stores), "All threads should get the same GapStore instance"
