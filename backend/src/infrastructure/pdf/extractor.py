"""
PDF Text Extractor using PyMuPDF (fitz).

Extracts text content from PDF files for NER processing.
"""

from dataclasses import dataclass, field
from pathlib import Path

import fitz

from src.domain.exceptions.extraction import InvalidPDFError
from src.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass(slots=True)
class PDFPage:
    """Extracted content from a single PDF page."""

    page_number: int
    text: str
    char_count: int


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""

    filename: str
    total_pages: int
    total_chars: int
    pages: list[PDFPage] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        """Get concatenated text from all pages."""
        return "\n\n".join(page.text for page in self.pages)


class PDFExtractor:
    """
    PDF text extractor using PyMuPDF.

    Extracts text content from PDF files, handling various formats
    and edge cases gracefully.
    """

    def __init__(self, max_pages: int | None = None) -> None:
        """
        Initialize PDF extractor.

        Args:
            max_pages: Maximum number of pages to extract (None = all pages)
        """
        self._max_pages = max_pages

    def extract_from_bytes(self, content: bytes, filename: str = "document.pdf") -> PDFExtractionResult:
        """
        Extract text from PDF bytes.

        Args:
            content: Raw PDF bytes
            filename: Original filename for logging/metadata

        Returns:
            PDFExtractionResult with extracted text

        Raises:
            InvalidPDFError: If PDF cannot be read or is corrupted
        """
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            logger.error("pdf_open_failed", filename=filename, error=str(e))
            raise InvalidPDFError(filename=filename, reason=str(e))

        return self._extract_from_document(doc, filename)

    def extract_from_file(self, file_path: str | Path) -> PDFExtractionResult:
        """
        Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            PDFExtractionResult with extracted text

        Raises:
            InvalidPDFError: If PDF cannot be read or is corrupted
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise InvalidPDFError(filename=str(file_path), reason="File not found")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error("pdf_open_failed", filename=str(file_path), error=str(e))
            raise InvalidPDFError(filename=str(file_path), reason=str(e))

        return self._extract_from_document(doc, file_path.name)

    def _extract_from_document(self, doc: fitz.Document, filename: str) -> PDFExtractionResult:
        """Extract text from an opened PyMuPDF document."""
        pages: list[PDFPage] = []
        total_chars = 0

        max_pages = self._max_pages or doc.page_count

        logger.info(
            "pdf_extraction_started",
            filename=filename,
            total_pages=doc.page_count,
            extracting_pages=min(max_pages, doc.page_count),
        )

        for page_num in range(min(max_pages, doc.page_count)):
            page = doc[page_num]
            text = page.get_text("text")

            text = self._clean_text(text)

            pages.append(
                PDFPage(
                    page_number=page_num + 1,
                    text=text,
                    char_count=len(text),
                )
            )
            total_chars += len(text)

        metadata = {}
        if doc.metadata:
            for key in ["title", "author", "subject", "keywords", "creator", "producer"]:
                if doc.metadata.get(key):
                    metadata[key] = doc.metadata[key]

        total_pages = doc.page_count
        doc.close()

        logger.info(
            "pdf_extraction_completed",
            filename=filename,
            pages_extracted=len(pages),
            total_chars=total_chars,
        )

        return PDFExtractionResult(
            filename=filename,
            total_pages=total_pages,
            total_chars=total_chars,
            pages=pages,
            metadata=metadata,
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)
