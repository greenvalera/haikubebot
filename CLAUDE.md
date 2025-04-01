# CLAUDE.md for HaikuBot

## Commands
- Install: `poetry install`
- Run: `poetry run start-bot` or `python haikubot.py`
- Format: `black .`
- Lint: `flake8 haikubot.py`
- Type check: `mypy haikubot.py`

## Code Style
- **Imports**: Group by stdlib, third-party, then local imports with a blank line between groups
- **Formatting**: Use Black with default settings
- **Types**: Use type hints for function parameters and return values
- **Naming**: 
  - Variables/functions: snake_case
  - Constants: UPPER_SNAKE_CASE
  - Classes: PascalCase
- **Error handling**: Use try/except blocks with specific exceptions
- **Documentation**: Add docstrings for functions and classes using triple quotes
- **Config**: Store configuration in config.json and environment variables in .env
- **Logging**: Use print statements with IS_DEBUG flag for development debugging