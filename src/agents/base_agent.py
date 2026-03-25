"""
Base agent for LangGraph pipeline.
Provides Gas Town session recording, OCC retry, LLM calls.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import urllib.request
import time
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from anthropic import AsyncAnthropic

MAX_OCC_RETRIES = 5


class BaseApexAgent(ABC):
    """
    Base for all Apex agents. Gas Town session management,
    per-node event recording, OCC retry scaffolding.
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        store,  # EventStore
        registry,  # ApplicantRegistryClient
        client: AsyncAnthropic,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.store = store
        self.registry = registry
        self.client = client
        self.model = model
        self.session_id: str | None = None
        self.application_id: str | None = None
        self._session_stream: str | None = None
        self._t0: float | None = None
        self._seq = 0
        self._llm_calls = 0
        self._tokens = 0
        self._cost = 0.0

    @abstractmethod
    def build_graph(self):
        raise NotImplementedError

    async def _append_with_retry(
        self,
        stream_id: str,
        events: list,
        expected_version: int | None = None,
        causation_id: str | None = None,
    ) -> int:
        """Append events with OCC retry. Pass expected_version=-1 for new streams."""
        for attempt in range(MAX_OCC_RETRIES):
            try:
                exp = expected_version
                if exp is None:
                    exists = await self.store.stream_exists(stream_id)
                    exp = -1 if not exists else await self.store.stream_version(stream_id)
                return await self.store.append(
                    stream_id=stream_id,
                    events=events,
                    expected_version=exp,
                    causation_id=causation_id,
                )
            except Exception as e:
                if "OptimisticConcurrencyError" in type(e).__name__ and attempt < MAX_OCC_RETRIES - 1:
                    await asyncio.sleep(0.1 * (2**attempt))
                    continue
                raise
        return -1

    async def _call_llm(
        self, system: str, user: str, max_tokens: int = 1024
    ) -> tuple[str, int, int, float]:
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        if openrouter_key:
            base_url = os.environ.get(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
            )
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }

            def _do_request():
                req = urllib.request.Request(
                    base_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    body = resp.read()
                return json.loads(body.decode("utf-8"))

            data = await asyncio.to_thread(_do_request)
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage") or {}
            i = int(usage.get("prompt_tokens") or 0)
            o = int(usage.get("completion_tokens") or 0)
            # Cost model here is best-effort; OpenRouter pricing varies by provider.
            cost = round(i / 1e6 * 3.0 + o / 1e6 * 15.0, 6)
            return text, i, o, cost

        # Fallback: Anthropic (keeps existing behavior).
        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = resp.content[0].text
        i = resp.usage.input_tokens
        o = resp.usage.output_tokens
        cost = round(i / 1e6 * 3.0 + o / 1e6 * 15.0, 6)
        return text, i, o, cost

    @staticmethod
    def _sha(d) -> str:
        return hashlib.sha256(json.dumps(str(d), sort_keys=True).encode()).hexdigest()[:16]
