"""
OpenRouter LLM Service.

Wraps langchain-openai's ChatOpenAI to point at the OpenRouter API.
Provides retry logic, model selection, and both sync/async invocation.
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from backend.config import settings

logger = logging.getLogger(__name__)


def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    streaming: bool = False,
) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance configured for OpenRouter.

    Parameters
    ----------
    model : str, optional
        OpenRouter model ID. Defaults to settings.DEFAULT_MODEL.
    temperature : float
        Sampling temperature (0.0 - 1.0).
    max_tokens : int
        Maximum tokens in the response.
    streaming : bool
        Whether to enable streaming responses.

    Returns
    -------
    ChatOpenAI
        Configured LLM client.
    """
    settings.validate()

    target_model = model or settings.DEFAULT_MODEL

    # If using Groq API, redirect non-Groq models to llama-3.3-70b-versatile
    if "groq" in settings.OPENROUTER_BASE_URL.lower():
        groq_models = {"llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"}
        if target_model not in groq_models:
            target_model = "llama-3.3-70b-versatile"
    else:
        # OpenRouter fallback mapping
        if target_model == "qwen/qwen-2.5-7b-instruct":
            target_model = "qwen/qwen-2.5-7b-instruct:free"
        discontinued_free_models = {
            "google/gemma-3-27b-it:free",
            "google/gemini-2.5-flash:free",
        }
        if target_model in discontinued_free_models:
            target_model = "openrouter/free"

    return ChatOpenAI(
        model=target_model,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": settings.APP_NAME,
        },
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def invoke_llm(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Invoke the LLM with retry logic.

    Parameters
    ----------
    prompt : str
        The user/human prompt to send.
    model : str, optional
        Model override.
    temperature : float
        Sampling temperature.
    max_tokens : int
        Max response tokens.
    system_prompt : str, optional
        System message to prepend.

    Returns
    -------
    str
        The LLM's text response.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(model=model, temperature=temperature, max_tokens=max_tokens)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    target_model = model or settings.DEFAULT_MODEL
    logger.info(f"Invoking LLM [{target_model}] ...")

    try:
        response = await llm.ainvoke(messages)
        logger.info("LLM response received.")
        return response.content
    except Exception as e:
        logger.error(f"LLM call failed [{target_model}]: {type(e).__name__}: {e}")
        raise


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def invoke_llm_json(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Invoke the LLM expecting a JSON response.

    Adds explicit instruction for JSON output format.
    Returns raw string (caller is responsible for parsing).
    """
    json_instruction = (
        "\n\nIMPORTANT: Respond ONLY with valid JSON. "
        "No markdown code fences, no explanation text outside the JSON."
    )
    full_prompt = prompt + json_instruction

    return await invoke_llm(
        prompt=full_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )
