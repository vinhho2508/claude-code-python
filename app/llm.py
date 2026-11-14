from openai import OpenAI
from app.config import Settings

class LLM:
    def __init__(self, settings: Settings):
        self._client = OpenAI(api_key=settings.api_key, base_url= settings.base_url)
        self._model = settings.model

    def chat(self, messages: list[dict], tools: list[dict]):
        return self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools
        )
