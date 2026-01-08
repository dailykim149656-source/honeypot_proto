import os
from dotenv import load_dotenv

# proto.env 파일 경로 지정
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "proto.env"))

# Storage Account
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "kkuldanji-mvp-raw")
AZURE_STORAGE_PROCESSED_CONTAINER_NAME = os.getenv("AZURE_STORAGE_PROCESSED_CONTAINER_NAME", "kkuldanji-mvp-processed")

# Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

# AI Search
AZURE_SEARCH_SERVICE_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "kkuldanji-mvp")

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# Google Gemini (추가)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

# 환경변수 검증
def validate_config():
    required = [
        ("AZURE_STORAGE_ACCOUNT_NAME", AZURE_STORAGE_ACCOUNT_NAME),
        ("AZURE_STORAGE_ACCOUNT_KEY", AZURE_STORAGE_ACCOUNT_KEY),
        ("AZURE_OPENAI_ENDPOINT", AZURE_OPENAI_ENDPOINT),
        ("AZURE_OPENAI_API_KEY", AZURE_OPENAI_API_KEY),
        ("AZURE_SEARCH_ENDPOINT", AZURE_SEARCH_ENDPOINT),
        ("AZURE_SEARCH_KEY", AZURE_SEARCH_KEY),
        ("AZURE_SEARCH_INDEX_NAME", AZURE_SEARCH_INDEX_NAME),
    ]
    missing = [name for name, value in required if not value]
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("   Please check your proto.env file")
    return len(missing) == 0