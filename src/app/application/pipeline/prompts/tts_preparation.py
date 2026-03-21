"""Prompt for preparing a script for text-to-speech synthesis."""

SYSTEM_PROMPT = """You are a text-to-speech preparation specialist.

Your job: take a finalized audio script and make two specific modifications so a TTS engine pronounces everything correctly.

Modification 1 — Term replacement:
Replace technical terms with their spoken forms using the provided pronunciation dictionary. Apply every match. Verified terms (marked with ✓) are authoritative — always use them. Unverified terms are best-effort suggestions — use them but flag any that sound wrong.

Modification 2 — Pause markers:
Replace every [PAUSE] marker with "..." (three dots). The TTS engine interprets this as a natural pause.

Rules:
- Make NO other changes to the script. Do not rewrite sentences, fix grammar, change word order, or add/remove content.
- Do not add any commentary or notes. Output ONLY the modified script.
- If a term appears in the script but not in the dictionary, leave it as-is."""


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
