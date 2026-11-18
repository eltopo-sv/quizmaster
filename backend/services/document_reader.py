
from pathlib import Path
import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def read_document(file_path: str) -> str:
    """
    Extrae texto de documentos PDF y DOCX.
    Devuelve el texto limpio.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Formato no permitido. Utiliza PDF o DOCX.")

    if extension == ".pdf":
        text = _read_pdf(path)
    else:
        text = _read_docx(path)

    text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )

    if len(text) < 50:
        raise ValueError(
            "El documento contiene muy poco texto. "
            "Comprueba que no sea un PDF escaneado."
        )

    return text


def _read_pdf(path: Path) -> str:
    text_parts = []

    with pymupdf.open(path) as document:
        for page in document:
            text_parts.append(page.get_text())

    return "\n".join(text_parts)


def _read_docx(path: Path) -> str:
    document = Document(path)

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    for table in document.tables:
        for row in table.rows:
            paragraphs.append(
                " | ".join(cell.text.strip() for cell in row.cells)
            )

    return "\n".join(paragraphs)
