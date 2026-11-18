
from abc import ABC, abstractmethod


class AIProviderError(Exception):
    """Error controlado de un proveedor de inteligencia artificial."""

    def __init__(
        self,
        message: str,
        retryable: bool = False,
        status_code: int | None = None
    ):
        self.message = message
        self.retryable = retryable
        self.status_code = status_code

        super().__init__(message)


class AIProvider(ABC):
    """Interfaz común para los proveedores de IA."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Envía una petición al proveedor y devuelve
        el contenido generado.
        """
        raise NotImplementedError
