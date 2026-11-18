
import os

import httpx
from dotenv import load_dotenv

from backend.services.providers.base import (
    AIProvider,
    AIProviderError
)

load_dotenv()


class GroqProvider(AIProvider):

    def __init__(self):

        self.api_key = os.getenv("GROQ_API_KEY")

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )

        self.url = "https://api.groq.com/openai/v1/chat/completions"

        self.timeout = 90.0

    async def generate(self, prompt: str) -> str:

        if not self.api_key:
            raise AIProviderError(
                "Falta configurar GROQ_API_KEY.",
                retryable=False
            )

        if not prompt.strip():
            raise AIProviderError(
                "El prompt está vacío.",
                retryable=False
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_completion_tokens": 8192,
            "include_reasoning": False
        }

        try:

            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    self.url,
                    headers=headers,
                    json=payload
                )

            if response.status_code >= 400:

                retryable = response.status_code in (
                    408, 429, 500, 502, 503, 504
                )

                raise AIProviderError(
                    f"Groq HTTP {response.status_code}: "
                    f"{response.text[:500]}",
                    retryable=retryable,
                    status_code=response.status_code
                )

            try:
                data = response.json()

            except ValueError as exc:
                raise AIProviderError(
                    "Groq ha devuelto una respuesta que no es JSON.",
                    retryable=True
                ) from exc

            choices = data.get("choices", [])

            if not choices:
                raise AIProviderError(
                    f"Groq no ha devuelto respuestas. "
                    f"Respuesta: {str(data)[:500]}",
                    retryable=True
                )

            choice = choices[0]
            message = choice.get("message", {})

            result = message.get("content")

            # Algunas respuestas pueden venir como lista de bloques.
            if isinstance(result, list):

                text_parts = []

                for item in result:

                    if isinstance(item, dict):

                        item_text = item.get("text")

                        if item_text:
                            text_parts.append(str(item_text))

                result = "\n".join(text_parts)

            # Comprobamos que el contenido sea texto.
            if not isinstance(result, str):
                result = ""

            result = result.strip()

            if not result:

                finish_reason = choice.get("finish_reason")
                message_keys = list(message.keys())
                usage = data.get("usage", {})

                raise AIProviderError(
                    "Groq ha devuelto el contenido vacío. "
                    f"Modelo: {self.model}. "
                    f"Motivo de finalización: {finish_reason}. "
                    f"Campos recibidos: {message_keys}. "
                    f"Uso de tokens: {usage}",
                    retryable=True
                )

            return result

        except httpx.TimeoutException as exc:

            raise AIProviderError(
                "Tiempo de espera agotado en Groq.",
                retryable=True
            ) from exc

        except httpx.RequestError as exc:

            raise AIProviderError(
                f"Error de conexión con Groq: {exc}",
                retryable=True
            ) from exc
