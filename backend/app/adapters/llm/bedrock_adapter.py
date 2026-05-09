"""AWS Bedrock LLM adapter for embedding + chat."""

from __future__ import annotations

import json
import os

from .base import LLMAdapter

DEFAULT_EMBED_MODEL = "amazon.titan-embed-text-v2:0"
DEFAULT_CHAT_MODEL = "anthropic.claude-3-haiku-20240307-v1:0"


class BedrockAdapter(LLMAdapter):
    """AWS Bedrock-backed LLM for embeddings and chat."""

    def __init__(
        self,
        embed_model: str | None = None,
        chat_model: str | None = None,
        region: str | None = None,
    ):
        self._embed_model = embed_model or os.getenv("BEDROCK_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self._chat_model = chat_model or os.getenv("BEDROCK_CHAT_MODEL", DEFAULT_CHAT_MODEL)
        self._region = region or os.getenv("AWS_REGION", "us-east-1")

        import boto3

        self._client = boto3.client("bedrock-runtime", region_name=self._region)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via Bedrock Titan Embeddings."""
        embeddings = []
        for text in texts:
            body = json.dumps({"inputText": text})
            response = self._client.invoke_model(
                modelId=self._embed_model,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        return embeddings

    def chat(self, messages: list[dict]) -> str:
        """Send chat via Bedrock Claude and return the assistant response."""
        # Separate system message from user/assistant messages
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append({"role": msg["role"], "content": msg["content"]})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "messages": chat_messages,
        }
        if system_text:
            body["system"] = system_text

        response = self._client.invoke_model(
            modelId=self._chat_model,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]
