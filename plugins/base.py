"""
Base class for HaikuBot plugins.
"""

from telegram.ext import Application


class BasePlugin:
    """Base class that all plugins must inherit from."""

    name: str = "unnamed"
    description: str = ""

    def __init__(self, config: dict):
        """
        Initialize the plugin with its config section.

        Args:
            config: The plugin's configuration dict from config.json
        """
        self.config = config
        self.enabled = config.get("enabled", True)

    def register(self, application: Application) -> None:
        """
        Register this plugin's handlers with the Telegram application.

        Subclasses MUST override this method to add their handlers.

        Args:
            application: The python-telegram-bot Application instance
        """
        raise NotImplementedError("Plugins must implement register()")
