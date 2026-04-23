from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_HOST = os.getenv("API_HOST", "http://127.0.0.1:8000")