"""
LLM Prompts Module.

Contains all prompts used for LLM interactions.
"""

from src.prompts.ner_extraction import (
    NER_SYSTEM_PROMPT,
    NER_USER_PROMPT_TEMPLATE,
    get_ner_system_prompt,
    get_ner_user_prompt,
)

__all__ = [
    "NER_SYSTEM_PROMPT",
    "NER_USER_PROMPT_TEMPLATE",
    "get_ner_system_prompt",
    "get_ner_user_prompt",
]
