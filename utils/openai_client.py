"""
OpenAI client and related functions
"""
from openai import OpenAI
from dotenv import load_dotenv
from .config import ANSWER_MODEL
# Initialize OpenAI client
client = OpenAI()

def invoke_model(prompt: str, model: str = ANSWER_MODEL) -> str:
    """
    Invoke OpenAI model with the given prompt.
    
    Args:
        prompt: The prompt to send to the model.
        model: The OpenAI model to use.
        
    Returns:
        str: The model's response.
    """
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()
