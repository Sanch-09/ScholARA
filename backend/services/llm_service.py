"""
ScholARA — LLM Service
Wraps Ollama (primary) and HuggingFace (fallback) with
streaming support and domain-specific prompt engineering.

If neither Ollama nor HuggingFace is available, falls back to
a built-in extractive mode so the app still works end-to-end.
"""

import httpx
import json
import asyncio
from typing import AsyncGenerator, List, Dict, Optional
from loguru import logger

from backend.core.config import settings

# ── System Prompt — Domain Specialization ─────────────────────────────────────
# This is the "simulated fine-tuning" approach:
# A carefully crafted system prompt that gives the model a research expert persona,
# few-shot examples, and response format guidelines.

RESEARCH_SYSTEM_PROMPT = """You are ScholARA, an expert AI research assistant specializing in academic research papers, scientific literature, and academic writing.

## Your Expertise
- Analyzing and explaining research methodologies
- Summarizing findings from academic papers
- Explaining technical concepts in clear language
- Identifying key contributions and limitations of research
- Connecting ideas across multiple papers

## Response Guidelines
1. **Be precise**: Base your answers strictly on the provided context documents
2. **Cite sources**: Always mention which document/section your information comes from
3. **Be honest**: If the answer is not in the provided context, say "I cannot find this information in the uploaded documents"
4. **Structure**: Use clear formatting with bullet points or numbered lists when appropriate
5. **Academic tone**: Maintain a professional, academic tone

## Context Format
You will receive retrieved chunks from research papers. Each chunk includes its source.
Always reference the source in your answer using format: [Source: filename, chunk N]

## Few-Shot Examples

User: "What is the main contribution of this paper?"
Assistant: Based on the abstract and introduction sections, the main contribution is [specific finding]. [Source: paper.pdf, chunk 1]

User: "What methodology was used?"
Assistant: The researchers employed [methodology]. Specifically, they [details]. [Source: paper.pdf, chunk 3]

User: "What are the limitations?"
Assistant: The authors acknowledge several limitations:
1. [Limitation 1] [Source: paper.pdf, chunk 8]
2. [Limitation 2] [Source: paper.pdf, chunk 9]

Remember: Only answer from the provided context. Be accurate, clear, and cite your sources."""


class LLMService:
    """
    Handles LLM inference with:
    - Ollama (local, free, recommended)
    - HuggingFace Inference API (free tier fallback)
    - Built-in extractive mode (always-available fallback)
    - Streaming support
    - Prompt engineering for research domain
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._ollama_available: Optional[bool] = None
        logger.info(f"LLM Service initialized: provider={self.provider}, model={self._get_model()}")

    def _get_model(self) -> str:
        if self.provider == "ollama":
            return settings.OLLAMA_MODEL
        return settings.HUGGINGFACE_MODEL

    def build_rag_prompt(
        self,
        query: str,
        context_chunks: List[Dict],
        chat_history: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        Build the full message list for the LLM including:
        - System prompt (domain persona)
        - Chat history (memory)
        - Retrieved context (RAG)
        - Current query
        """
        messages = [{"role": "system", "content": RESEARCH_SYSTEM_PROMPT}]

        # Add recent chat history (last 6 messages for context window management)
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Build context block from retrieved chunks
        if context_chunks:
            context_text = "\n\n---\n\n".join([
                f"[Source: {c['filename']}, chunk {c['chunk_index'] + 1}]\n{c['content']}"
                for c in context_chunks
            ])
            context_message = f"""## Retrieved Context from Research Documents

{context_text}

---
Based on the above context, please answer the following question:
"""
        else:
            context_message = "No relevant context was found in the uploaded documents. Please answer based on general knowledge or inform the user.\n\n"

        # Add context + query as user message
        messages.append({
            "role": "user",
            "content": context_message + query
        })

        return messages

    async def generate_response(
        self,
        messages: List[Dict],
        stream: bool = False,
    ) -> str:
        """Generate a response from the LLM (non-streaming)."""
        # Try Ollama first
        if self.provider == "ollama":
            try:
                result = await self._ollama_generate(messages)
                self._ollama_available = True
                return result
            except Exception as e:
                logger.warning(f"Ollama unavailable, falling back: {e}")
                self._ollama_available = False

        # Try HuggingFace
        if settings.HUGGINGFACE_API_TOKEN and settings.HUGGINGFACE_API_TOKEN != "hf_your_token_here":
            try:
                return await self._huggingface_generate(messages)
            except Exception as e:
                logger.warning(f"HuggingFace unavailable, falling back to built-in: {e}")

        # Built-in extractive fallback
        return self._builtin_extractive_response(messages)

    async def stream_response(
        self,
        messages: List[Dict],
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens from the LLM."""
        # Try Ollama streaming
        if self.provider == "ollama" and self._ollama_available is not False:
            try:
                has_tokens = False
                async for token in self._ollama_stream(messages):
                    has_tokens = True
                    yield token
                if has_tokens:
                    self._ollama_available = True
                    return
            except Exception as e:
                logger.warning(f"Ollama stream failed, falling back: {e}")
                self._ollama_available = False

        # Fallback: generate full response, then simulate streaming
        response = await self.generate_response(messages)
        words = response.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.02)  # Simulate typing delay

    async def _ollama_generate(self, messages: List[Dict]) -> str:
        """Call Ollama local API (non-streaming)."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,   # Lower = more factual
                            "top_p": 0.9,
                            "num_predict": 1024,
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]

        except httpx.ConnectError:
            logger.error("Ollama not running. Start with: ollama serve")
            raise RuntimeError(
                "Ollama is not running. Please start it with 'ollama serve' "
                "and ensure the model is pulled: 'ollama pull llama3.2'"
            )
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")

    async def _ollama_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": True,
                        "options": {"temperature": 0.3, "num_predict": 1024},
                    },
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                token = data.get("message", {}).get("content", "")
                                if token:
                                    yield token
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue

        except httpx.ConnectError:
            yield "\n\n[Error: Ollama is not running. Please start with 'ollama serve']"

    async def _huggingface_generate(self, messages: List[Dict]) -> str:
        """
        Call HuggingFace Inference API (free tier).
        Converts chat format to a single prompt string.
        """
        if not settings.HUGGINGFACE_API_TOKEN:
            raise RuntimeError("HUGGINGFACE_API_TOKEN not set in .env")

        # Convert messages to a prompt
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"<s>[INST] <<SYS>>\n{msg['content']}\n<</SYS>>\n\n"
            elif msg["role"] == "user":
                prompt += f"{msg['content']} [/INST]"
            elif msg["role"] == "assistant":
                prompt += f"{msg['content']}</s><s>[INST]"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"https://api-inference.huggingface.co/models/{settings.HUGGINGFACE_MODEL}",
                    headers={"Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}"},
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 512,
                            "temperature": 0.3,
                            "return_full_text": False,
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data[0]["generated_text"]

        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            raise RuntimeError(f"HuggingFace generation failed: {e}")

    def _builtin_extractive_response(self, messages: List[Dict]) -> str:
        """
        Built-in fallback: creates an intelligent extractive response from
        the retrieved context chunks when no external LLM is available.
        This ensures the app works end-to-end even without Ollama.
        """
        # Extract the user message (last one) and context
        user_msg = ""
        context_chunks = []

        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]

        # Parse context from the user message
        if "## Retrieved Context from Research Documents" in user_msg or "## Context" in user_msg:
            if "## Retrieved Context" in user_msg:
                parts = user_msg.split("---\nBased on the above context, please answer the following question:\n")
                header_text = "## Retrieved Context from Research Documents\n\n"
            else:
                parts = user_msg.split("\n\n## Question\n")
                header_text = "## Context\n"
            
            if len(parts) >= 2:
                context_section = parts[0]
                query = parts[-1].strip()

                # Extract individual chunks
                chunk_blocks = context_section.split("\n\n---\n\n")
                for block in chunk_blocks:
                    block = block.replace(header_text, "")
                    if block.strip():
                        context_chunks.append(block.strip())
            else:
                query = user_msg
        else:
            query = user_msg

        if not context_chunks:
            return (
                "I don't have any relevant context from uploaded documents to answer your question. "
                "Please upload a research paper first, then ask me about it.\n\n"
                "*Note: ScholARA is running in built-in mode (no external LLM detected). "
                "For richer responses, install [Ollama](https://ollama.ai) and run: "
                "`ollama serve` then `ollama pull qwen2.5:7b`*"
            )

        # Build an intelligent extractive response
        query_lower = query.lower()

        # Identify query type and format response accordingly
        response_parts = []

        if any(kw in query_lower for kw in ["summary", "summarize", "overview", "about", "main"]):
            response_parts.append(f"**Summary based on retrieved context:**\n")
        elif any(kw in query_lower for kw in ["method", "approach", "technique", "how"]):
            response_parts.append(f"**Methodology details from the documents:**\n")
        elif any(kw in query_lower for kw in ["result", "finding", "conclusion", "outcome"]):
            response_parts.append(f"**Key findings from the documents:**\n")
        elif any(kw in query_lower for kw in ["limitation", "weakness", "challenge", "problem"]):
            response_parts.append(f"**Limitations identified in the documents:**\n")
        elif any(kw in query_lower for kw in ["future", "suggest", "recommend"]):
            response_parts.append(f"**Future work and suggestions from the documents:**\n")
        else:
            response_parts.append(f"**Based on the retrieved context, here is the relevant information:**\n")

        # Add relevant context chunks
        for i, chunk in enumerate(context_chunks[:5]):
            # Extract source info and content
            lines = chunk.split("\n", 1)
            source_line = lines[0] if lines[0].startswith("[Source:") else ""
            content = lines[1] if len(lines) > 1 else lines[0]

            if source_line:
                content = content.strip()
                # Trim long content
                if len(content) > 400:
                    content = content[:400].rsplit(" ", 1)[0] + "..."
                response_parts.append(f"{i + 1}. {content}\n   {source_line}\n")
            else:
                if len(chunk) > 400:
                    chunk = chunk[:400].rsplit(" ", 1)[0] + "..."
                response_parts.append(f"{i + 1}. {chunk}\n")

        response_parts.append(
            "\n---\n*⚡ Running in built-in extractive mode. "
            "For AI-generated answers, install Ollama: `ollama serve` → `ollama pull qwen2.5:7b`*"
        )

        return "\n".join(response_parts)

    async def check_health(self) -> Dict:
        """Check if the LLM backend is reachable."""
        if self.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                    models = resp.json().get("models", [])
                    model_names = [m["name"] for m in models]
                    self._ollama_available = True
                    return {
                        "status": "ok",
                        "provider": "ollama",
                        "available_models": model_names,
                        "selected_model": settings.OLLAMA_MODEL,
                        "model_ready": settings.OLLAMA_MODEL in model_names or
                                       any(settings.OLLAMA_MODEL in m for m in model_names),
                    }
            except Exception as e:
                self._ollama_available = False
                return {
                    "status": "degraded",
                    "provider": "builtin-extractive",
                    "note": "Ollama not available — using built-in extractive mode",
                    "error": str(e),
                }
        return {"status": "ok", "provider": "huggingface"}


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
