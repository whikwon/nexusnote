from app.core.config import settings


class _LLMSingleton:
    _instance = None
    llm = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_LLMSingleton, cls).__new__(cls)
            cls._instance.llm = settings.LLM_CLS(**settings.LLM_KWARGS)
        return cls._instance


def get_llm():
    return _LLMSingleton().llm


def init_llm():
    _LLMSingleton()
