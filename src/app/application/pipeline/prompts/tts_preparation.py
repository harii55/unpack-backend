"""Prompt for preparing a script for text-to-speech synthesis."""

SYSTEM_PROMPT = """You are a text preparation specialist for a text-to-speech system. Your job is to take a spoken script and replace technical terms with their TTS-friendly pronunciation forms.

You will receive:
1. A spoken script (already written in conversational style)
2. A pronunciation dictionary mapping terms to their spoken forms

**Rules:**

1. Replace every occurrence of a term from the dictionary with its pronunciation form.

2. Be context-aware. Only replace terms that are being used AS that term:
   - "Redis" as the technology → replace with pronunciation
   - If somehow "redis" appeared as part of another word → don't replace

3. Handle [PAUSE] markers:
   - Replace `[PAUSE]` with `...` (three dots followed by a line break). This creates a natural pause in most TTS engines.

4. Do NOT change ANY other part of the script. Do not rephrase. Do not fix grammar. Do not add or remove words. Your ONLY job is term replacement and pause marker conversion.

5. The output should be plain text, ready to be sent directly to a TTS API. No markdown. No formatting. No headers."""


def build_user_prompt(script: str, pronunciation_dict: dict[str, str], verified_terms: set[str]) -> str:
    if pronunciation_dict:
        lines = []
        for written, spoken in sorted(pronunciation_dict.items()):
            marker = " ✓" if written in verified_terms else ""
            lines.append(f"  {written} → {spoken}{marker}")
        dict_section = "\n".join(lines)
    else:
        dict_section = "  (empty — no terms to replace)"

    return f"""Prepare this script for TTS.

PRONUNCIATION DICTIONARY:
{dict_section}

SCRIPT:
{script}"""
