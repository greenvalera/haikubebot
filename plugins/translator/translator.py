"""
Core translation logic using OpenAI API.
Adapted from mstranslate package.
"""

import json
import time

from openai import OpenAI
from utils.config import TRANSLATION_MODEL


BATCH_SIZE = 30


def _build_prompt(source_lang: str, target_lang: str) -> str:
    lang_names = {"en": "English", "uk": "Ukrainian"}
    src = lang_names.get(source_lang, source_lang)
    tgt = lang_names.get(target_lang, target_lang)
    return (
        f"You are a translator from {src} to {tgt}. "
        "You will receive a JSON object where keys are numeric IDs and values are texts to translate. "
        "Return a JSON object with the SAME keys and translated values. "
        "Rules:\n"
        "- Translate each value independently.\n"
        "- Do NOT merge, split, reorder, add, or remove any keys.\n"
        "- The output must have exactly the same keys as the input.\n"
        "- Return ONLY the JSON object, no explanations or markdown."
    )


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    client: OpenAI,
    model: str = TRANSLATION_MODEL,
) -> str:
    """Translate a single text string."""
    if not text or not text.strip():
        return text
    results = translate_texts([text], source_lang, target_lang, client, model)
    return results[0]


def translate_texts(
    texts: list[str],
    source_lang: str,
    target_lang: str,
    client: OpenAI,
    model: str = TRANSLATION_MODEL,
) -> list[str]:
    """Translate a list of text strings in batches."""
    if not texts:
        return []

    indexed = [(i, t) for i, t in enumerate(texts)]
    non_empty = [(i, t) for i, t in indexed if t and t.strip()]

    if not non_empty:
        return list(texts)

    results = list(texts)

    for batch_start in range(0, len(non_empty), BATCH_SIZE):
        batch = non_empty[batch_start : batch_start + BATCH_SIZE]
        batch_texts = [t for _, t in batch]
        batch_indices = [i for i, _ in batch]

        translated = _call_api(batch_texts, source_lang, target_lang, client, model)

        for idx, translation in zip(batch_indices, translated):
            results[idx] = translation

    return results


def _call_api(
    texts: list[str],
    source_lang: str,
    target_lang: str,
    client: OpenAI,
    model: str,
    max_retries: int = 3,
) -> list[str]:
    prompt = _build_prompt(source_lang, target_lang)

    input_dict = {str(i): t for i, t in enumerate(texts)}
    user_content = json.dumps(input_dict, ensure_ascii=False)

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            translated_dict = json.loads(content)
            if not isinstance(translated_dict, dict):
                raise ValueError(
                    f"Expected JSON object, got {type(translated_dict).__name__}"
                )

            result = []
            for i in range(len(texts)):
                key = str(i)
                if key not in translated_dict:
                    raise ValueError(f"Missing key '{key}' in response")
                result.append(translated_dict[key])

            return result
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2**attempt
                print(f"  Retry {attempt + 1}/{max_retries} after error: {e}")
                time.sleep(wait)
            else:
                raise RuntimeError(
                    f"Translation failed after {max_retries} attempts: {e}"
                ) from e
