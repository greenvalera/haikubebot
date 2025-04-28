"""
OpenAI client and related functions
"""
from openai import OpenAI
import os
from dotenv import load_dotenv
from .config import MODEL
# Initialize OpenAI client
client = OpenAI()

def invoke_model(prompt: str) -> str:
    """
    Invoke OpenAI model with the given prompt.
    
    Args:
        prompt: The prompt to send to the model.
        
    Returns:
        str: The model's response.
    """
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip() 