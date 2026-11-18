
import os

import httpx
from dotenv import load_dotenv

from backend.services.providers.base import (
    AIProvider,
    AIProviderError
)

load_dotenv()


class GeminiProvider(AIProvider):

    def __init__(self):

        self.api_key = os.getenv("GEMINI_API_KEY")

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        self.url = (
            "https://generativelanguage.googleapis.com"
            "/v1beta/interactions"
        )

        self.timeout = 90.0

    async def generate(self, prompt: str) -> str:

        if not self.api_key:
            raise AIProviderError(
                "Falta configurar GEMINI_API_KEY.",
                retryable=False
            )

        if not prompt.strip():
            raise AIProviderError(
                "El prompt está vacío.",
                retryable=False
            )

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": prompt,
            "store": False
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
                    f"Gemini HTTP {response.status_code}: "
                    f"{response.text[:500]}",
                    retryable=retryable,
                    status_code=response.status_code
                )

            data = response.json()

            # Compatibilidad con respuestas que incluyan output_text
            result = data.get("output_text", "")

            # Extracción del formato REST actual: steps
            if not result:

                text_parts = []

                for step in data.get("steps", []):

                    if step.get("type") != "model_output":
                        continue

                    for content in step.get("content", []):

                        if content.get("type") == "text":
                            text_parts.append(
                                content.get("text", "")
                            )

                result = "\n".join(
                    part for part in text_parts if part
                )

            if not result:

                raise AIProviderError(
                    "Gemini no ha devuelto texto válido.",
                    retryable=True
                )

            return result.strip()

        except httpx.TimeoutException as exc:

            raise AIProviderError(
                "Tiempo de espera agotado en Gemini.",
                retryable=True
            ) from exc

        except httpx.RequestError as exc:

            raise AIProviderError(
                f"Error de conexión con Gemini: {exc}",
                retryable=True
            ) from exc
