import os
import time
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Type, List, Optional, Union, Dict, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from openai import APIConnectionError

from medster.prompts import DEFAULT_SYSTEM_PROMPT


def call_llm(
    prompt: str,
    model: str = None,  # Auto-detect from env if not specified
    system_prompt: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    tools: Optional[List[BaseTool]] = None,
    images: Optional[List[str]] = None,
    reasoning_effort: str = "none",  # GPT-5.1 reasoning: none, low, medium, high
) -> AIMessage:
    """
    Call LLM (Claude or GPT) with the given prompt and configuration.

    Args:
        prompt: The user prompt to send
        model: LLM model to use (auto-detects from LLM_PROVIDER env var if not specified)
               Claude: claude-sonnet-4.5, claude-opus-4.5, claude-haiku-4
               OpenAI: gpt-5.1, gpt-5, gpt-4o
        system_prompt: Optional system prompt override
        output_schema: Optional Pydantic schema for structured output
        tools: Optional list of tools to bind
        images: Optional list of base64-encoded PNG images for vision analysis
        reasoning_effort: GPT-5.1 reasoning effort (none=fast, low, medium, high=thorough)

    Returns:
        AIMessage or structured output based on schema
    """
    final_system_prompt = system_prompt if system_prompt else DEFAULT_SYSTEM_PROMPT

    # Auto-detect model from environment if not specified
    if model is None:
        provider = os.getenv("LLM_PROVIDER", "claude").lower()
        if provider == "openai":
            model = os.getenv("LLM_MODEL", "gpt-5.1")
        else:
            model = os.getenv("LLM_MODEL", "claude-sonnet-4.5")

    # Determine provider from model name
    if model.startswith("gpt") or model.startswith("o1"):
        return _call_openai(
            prompt, model, final_system_prompt, output_schema, tools, images, reasoning_effort
        )
    else:
        return _call_claude(
            prompt, model, final_system_prompt, output_schema, tools, images
        )


def _call_claude(
    prompt: str,
    model: str,
    system_prompt: str,
    output_schema: Optional[Type[BaseModel]],
    tools: Optional[List[BaseTool]],
    images: Optional[List[str]],
) -> AIMessage:
    """Call Claude LLM via Anthropic API."""
    # Map model names to Anthropic model IDs
    model_mapping = {
        "claude-sonnet-4.5": "claude-sonnet-4-20250514",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-opus-4.5": "claude-opus-4-5-20251101",
        "claude-haiku-4": "claude-haiku-4-20250615",
    }

    anthropic_model = model_mapping.get(model, "claude-sonnet-4-20250514")

    # Initialize Claude LLM
    llm = ChatAnthropic(
        model=anthropic_model,
        temperature=0,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Add structured output or tools to the LLM
    runnable = llm
    if output_schema:
        runnable = llm.with_structured_output(output_schema, method="function_calling")
    elif tools:
        runnable = llm.bind_tools(tools)

    # Build messages based on whether images are included
    if images:
        # Multimodal message with images
        content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]

        # Add each image to content
        for img_base64 in images:
            content_parts.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_base64
                }
            })

        # Create multimodal message
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts}
        ]

        # Retry logic for transient connection errors
        for attempt in range(3):
            try:
                return runnable.invoke(messages)
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s backoff

    else:
        # Text-only message (original behavior)
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{prompt}")
        ])

        chain = prompt_template | runnable

        # Retry logic for transient connection errors
        for attempt in range(3):
            try:
                return chain.invoke({"prompt": prompt})
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s backoff


def _call_openai(
    prompt: str,
    model: str,
    system_prompt: str,
    output_schema: Optional[Type[BaseModel]],
    tools: Optional[List[BaseTool]],
    images: Optional[List[str]],
    reasoning_effort: str = "none",
) -> AIMessage:
    """Call OpenAI LLM (GPT-5.1, GPT-5, GPT-4o) via OpenAI API."""

    # Initialize OpenAI LLM with model_kwargs for reasoning
    model_kwargs = {}

    # GPT-5.1 and GPT-5 support reasoning effort parameter
    if model in ["gpt-5.1", "gpt-5"]:
        model_kwargs["reasoning"] = {"effort": reasoning_effort}

    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        model_kwargs=model_kwargs
    )

    # Add structured output or tools to the LLM
    runnable = llm
    if output_schema:
        runnable = llm.with_structured_output(output_schema, method="function_calling")
    elif tools:
        runnable = llm.bind_tools(tools)

    # Build messages based on whether images are included
    if images:
        # Multimodal message with images (GPT-4o, GPT-4-turbo support vision)
        content_parts: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]

        # Add each image to content (OpenAI format)
        for img_base64 in images:
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            })

        # Create multimodal message
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_parts}
        ]

        # Retry logic for transient connection errors
        for attempt in range(3):
            try:
                return runnable.invoke(messages)
            except APIConnectionError as e:
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s backoff

    else:
        # Text-only message
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{prompt}")
        ])

        chain = prompt_template | runnable

        # Retry logic for transient connection errors
        for attempt in range(3):
            try:
                return chain.invoke({"prompt": prompt})
            except APIConnectionError as e:
                if attempt == 2:  # Last attempt
                    raise
                time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s backoff
