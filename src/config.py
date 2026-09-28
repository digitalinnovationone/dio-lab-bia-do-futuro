import os
from dotenv import load_dotenv

# Procura o .env subindo as pastas a partir deste arquivo (funciona com o .env na raiz ou em src/)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

