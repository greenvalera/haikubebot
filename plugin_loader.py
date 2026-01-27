"""
Plugin loader for HaikuBot.
Discovers and loads enabled plugins from config.
"""

import importlib
import logging
from typing import List

from telegram.ext import Application

from plugins.base import BasePlugin


def load_plugins(
    application: Application, plugins_config: dict
) -> List[BasePlugin]:
    """
    Load enabled plugins and register their handlers.

    Args:
        application: The python-telegram-bot Application instance
        plugins_config: The "plugins" section from config.json

    Returns:
        List of loaded plugin instances
    """
    loaded = []

    for plugin_name, plugin_config in plugins_config.items():
        if not plugin_config.get("enabled", False):
            logging.info("Plugin '%s' is disabled, skipping", plugin_name)
            continue

        try:
            module = importlib.import_module(f"plugins.{plugin_name}")

            plugin_class = getattr(module, "plugin_class", None)
            if plugin_class is None:
                class_name = plugin_name.capitalize() + "Plugin"
                plugin_class = getattr(module, class_name)

            instance = plugin_class(plugin_config)
            instance.register(application)
            loaded.append(instance)
            logging.info("Plugin '%s' loaded successfully", plugin_name)

        except Exception as e:
            logging.error("Failed to load plugin '%s': %s", plugin_name, e)

    return loaded
