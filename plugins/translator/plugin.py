"""
Translator plugin for HaikuBot.
Translates .docx and .xlsx files.
"""

from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
    filters,
)

from plugins.base import BasePlugin
from .handlers import (
    handle_document,
    handle_language_choice,
    cancel_translation,
    WAITING_LANGUAGE,
)


class TranslatorPlugin(BasePlugin):
    """Plugin that translates .docx and .xlsx files."""

    name = "translator"
    description = "Translates .docx and .xlsx files to a chosen language"

    def register(self, application: Application) -> None:
        """Register the conversation handler for document translation."""
        docx_filter = filters.Document.MimeType(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        xlsx_filter = filters.Document.MimeType(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(docx_filter | xlsx_filter, handle_document),
            ],
            states={
                WAITING_LANGUAGE: [
                    CallbackQueryHandler(handle_language_choice),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_translation),
            ],
            per_user=True,
            per_chat=True,
        )
        application.add_handler(conv_handler)
