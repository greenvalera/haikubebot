"""
Handler functions for the translator plugin.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

from openai import OpenAI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

WAITING_LANGUAGE = 0

LANGUAGES = {
    "uk": "Українська",
    "en": "English",
}


async def handle_document(update: Update, context: CallbackContext) -> int:
    """Entry point: user sends a .docx or .xlsx file."""
    document = update.message.document
    file_name = document.file_name

    context.user_data["translate_file_id"] = document.file_id
    context.user_data["translate_file_name"] = file_name

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"translate:{code}")]
        for code, label in LANGUAGES.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Отримано файл: {file_name}\nНа яку мову перекласти?",
        reply_markup=reply_markup,
    )
    return WAITING_LANGUAGE


async def handle_language_choice(update: Update, context: CallbackContext) -> int:
    """User picked a target language via inline button."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data or not data.startswith("translate:"):
        return WAITING_LANGUAGE

    target_lang = data.split(":", 1)[1]
    target_label = LANGUAGES.get(target_lang, target_lang)

    file_id = context.user_data.get("translate_file_id")
    file_name = context.user_data.get("translate_file_name")

    if not file_id or not file_name:
        await query.edit_message_text(
            "Помилка: файл не знайдено. Надішліть файл ще раз."
        )
        return ConversationHandler.END

    await query.edit_message_text(f"Перекладаю '{file_name}' на {target_label}...")

    try:
        tg_file = await context.bot.get_file(file_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / file_name
            await tg_file.download_to_drive(str(input_path))

            stem = input_path.stem
            suffix = input_path.suffix
            output_name = f"{stem}_{target_lang}{suffix}"
            output_path = Path(tmpdir) / output_name

            source_lang = "uk" if target_lang == "en" else "en"

            await asyncio.to_thread(
                _translate_file, input_path, output_path, source_lang, target_lang
            )

            with open(output_path, "rb") as f:
                await query.message.reply_document(document=f, filename=output_name)

    except Exception as e:
        logging.error("Translation error: %s", e)
        await query.message.reply_text(f"Помилка перекладу: {e}")

    context.user_data.pop("translate_file_id", None)
    context.user_data.pop("translate_file_name", None)
    return ConversationHandler.END


def _translate_file(
    input_path: Path, output_path: Path, source_lang: str, target_lang: str
) -> None:
    """Synchronous translation wrapper."""
    from .docx_handler import translate_docx
    from .xlsx_handler import translate_xlsx

    client = OpenAI()
    model = "gpt-5.2"

    ext = input_path.suffix.lower()
    if ext == ".docx":
        translate_docx(input_path, output_path, source_lang, target_lang, client, model)
    elif ext == ".xlsx":
        translate_xlsx(input_path, output_path, source_lang, target_lang, client, model)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def cancel_translation(update: Update, context: CallbackContext) -> int:
    """Cancel the translation conversation."""
    context.user_data.pop("translate_file_id", None)
    context.user_data.pop("translate_file_name", None)
    await update.message.reply_text("Переклад скасовано.")
    return ConversationHandler.END
