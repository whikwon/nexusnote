from app.core.config import settings


def init_llm():
    return settings.LLM_CLS(**settings.LLM_KWARGS)
