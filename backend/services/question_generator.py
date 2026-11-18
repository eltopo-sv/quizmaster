
import json
import re

from backend.services.providers.manager import AIManager


class QuestionGenerator:

    def __init__(self):
        self.ai = AIManager()

    async def generate_questions(
        self,
        document_text: str,
        number: int,
        difficulty: str
    ) -> list:

        if not document_text or len(document_text.strip()) < 50:
            raise ValueError("El documento no contiene suficiente texto.")

        if not isinstance(number, int) or not 1 <= number <= 100:
            raise ValueError("El número debe estar entre 1 y 100.")

        difficulty = difficulty.lower().strip()

        if difficulty not in ("facil", "media", "dificil"):
            raise ValueError("Dificultad no válida.")

        prompt = f"""
Eres un experto en elaboración de preguntas educativas
para concursos por equipos.

Debes crear exactamente {number} preguntas.
Dificultad: {difficulty}.

UTILIZA EXCLUSIVAMENTE LA INFORMACIÓN DEL DOCUMENTO.
No inventes datos ni introduzcas información externa.
Si no hay información suficiente para crear todas las
preguntas, indícalo mediante una respuesta incompleta.

Cada pregunta debe tener:
- Un enunciado claro.
- Cuatro respuestas posibles.
- Una única respuesta correcta.
- Una explicación basada en el documento.

Devuelve EXCLUSIVAMENTE JSON válido con esta estructura:

{{
  "questions": [
    {{
      "text": "Enunciado",
      "option_a": "Respuesta A",
      "option_b": "Respuesta B",
      "option_c": "Respuesta C",
      "option_d": "Respuesta D",
      "correct_option": "B",
      "explanation": "Explicación de la respuesta"
    }}
  ]
}}

DOCUMENTO:

{document_text}
"""

        response = await self.ai.generate(prompt)

        questions = self._parse_response(response)

        if len(questions) != number:
            raise ValueError(
                f"Se solicitaron {number} preguntas, "
                f"pero la IA generó {len(questions)}."
            )

        return [
            self._validate_question(question)
            for question in questions
        ]

    def _parse_response(self, response: str) -> list:

        cleaned = response.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            data = None

            decoder = json.JSONDecoder()

            for position, character in enumerate(cleaned):
                if character not in "[{":
                    continue

                try:
                    data, _ = decoder.raw_decode(
                        cleaned[position:]
                    )
                    break
                except json.JSONDecodeError:
                    continue

            if data is None:
                raise ValueError(
                    "La IA no ha devuelto JSON válido."
                )

        if isinstance(data, dict):
            questions = data.get(
                "questions",
                data.get("preguntas")
            )
        else:
            questions = data

        if not isinstance(questions, list):
            raise ValueError(
                "La respuesta no contiene una lista de preguntas."
            )

        return questions

    def _validate_question(self, question: dict) -> dict:

        if not isinstance(question, dict):
            raise ValueError("Pregunta con formato incorrecto.")

        fields = [
            "text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_option",
            "explanation"
        ]

        for field in fields:
            value = question.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Pregunta incompleta: falta {field}."
                )

        correct = question["correct_option"].strip().upper()

        if correct not in ("A", "B", "C", "D"):
            raise ValueError("Respuesta correcta no válida.")

        options = [
            question["option_a"].strip(),
            question["option_b"].strip(),
            question["option_c"].strip(),
            question["option_d"].strip()
        ]

        if len({option.casefold() for option in options}) != 4:
            raise ValueError(
                "La pregunta contiene respuestas duplicadas."
            )

        return {
            "text": question["text"].strip(),
            "option_a": options[0],
            "option_b": options[1],
            "option_c": options[2],
            "option_d": options[3],
            "correct_option": correct,
            "explanation": question["explanation"].strip(),
            "verified": False
        }
