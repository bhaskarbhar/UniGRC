import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek/deepseek-chat-v3-0324:free"

MONGODB_URI = os.getenv("MONGODB_URI")

# MongoDB setup
client = AsyncIOMotorClient(MONGODB_URI)
db = client.unigrc

# Collection map
collections_map = {
    "iso": db.iso,
    "nist": db.nist,
    "cis": db.cis,
}
