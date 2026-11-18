
import os
from dotenv import load_dotenv

from backend.services.providers.base import AIProviderError
from backend.services.providers.gemini import GeminiProvider
from backend.services.providers.groq import GroqProvider


load_dotenv()


class AIManager:

    def __init__(self):

        self.preferred = os.getenv(
            "AI_PROVIDER", "gemini"
        ).lower()

        self.providers = {
            "gemini": GeminiProvider(),
            "groq": GroqProvider()
        }

        if self.preferred not in self.providers:
            raise ValueError(
                f"Proveedor no reconocido: {self.preferred}"
            )

    async def generate(self, prompt: str) -> str:

        primary_name = self.preferred

        backup_name = (
            "groq" if primary_name == "gemini"
            else "gemini"
        )

        primary = self.providers[primary_name]
        backup = self.providers[backup_name]

        try:
            print(f"QUIZMASTER: utilizando {primary_name}")
            return await primary.generate(prompt)

        except AIProviderError as error:

            if not error.retryable:
                raise

            print(
                f"{primary_name} no disponible: {error}"
            )

            print(
                f"QUIZMASTER: activando {backup_name}"
            )

            try:
                return await backup.generate(prompt)

            except AIProviderError as backup_error:

                raise AIProviderError(
                    f"Los dos proveedores han fallado. "
                    f"{primary_name}: {error}. "
                    f"{backup_name}: {backup_error}",
                    retryable=backup_error.retryable
                ) from backup_error
