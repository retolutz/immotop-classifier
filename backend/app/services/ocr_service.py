"""
OCR Service für Schweizer Rechnungen

Unterstützt:
- PDF (Text-Extraktion via PyPDF2)
- Bilder (benötigt lokales Tesseract - auf Azure deaktiviert)
"""

import io
import re
from typing import Optional
from datetime import date
from decimal import Decimal
from pathlib import Path

from PyPDF2 import PdfReader

from app.models.invoice import InvoiceData

# Optionale Imports für lokale Entwicklung
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class OCRService:
    """Service für OCR-Extraktion aus Rechnungen"""

    def __init__(self, lang: str = "deu"):
        self.lang = lang

    async def extract_from_bytes(
        self, file_bytes: bytes, filename: str
    ) -> InvoiceData:
        """Extrahiert Text und Daten aus einer Datei"""
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            raw_text = await self._extract_from_pdf(file_bytes)
        elif extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            raw_text = await self._extract_from_image(file_bytes)
        else:
            raise ValueError(f"Nicht unterstütztes Format: {extension}")

        # Strukturierte Daten extrahieren
        return self._parse_invoice_text(raw_text)

    async def _extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extrahiert Text aus PDF"""
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

        full_text = "\n".join(text_parts)

        if len(full_text.strip()) < 10:
            return "PDF enthält keinen extrahierbaren Text. Bitte als digitale Rechnung hochladen."

        return full_text

    async def _extract_from_image(self, image_bytes: bytes) -> str:
        """OCR aus Bilddatei - benötigt Tesseract"""
        if not OCR_AVAILABLE:
            return "Bild-OCR ist in der Cloud-Version nicht verfügbar. Bitte laden Sie PDFs mit eingebettetem Text hoch."

        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image, lang=self.lang)

    def _parse_invoice_text(self, raw_text: str) -> InvoiceData:
        """Extrahiert strukturierte Daten aus dem Text"""
        data = InvoiceData(raw_text=raw_text)

        # Betrag extrahieren (CHF/Fr./Franken)
        data.bruttobetrag = self._extract_amount(raw_text)

        # Datum extrahieren
        data.rechnungsdatum = self._extract_date(raw_text)

        # IBAN extrahieren
        data.iban = self._extract_iban(raw_text)

        # QR-Referenz extrahieren
        data.qr_referenz = self._extract_qr_reference(raw_text)

        # Rechnungsnummer extrahieren
        data.rechnungsnummer = self._extract_invoice_number(raw_text)

        # MWST extrahieren
        mwst_info = self._extract_mwst(raw_text)
        if mwst_info:
            data.mwst_betrag = mwst_info.get("betrag")
            data.mwst_satz = mwst_info.get("satz")

        return data

    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extrahiert den Gesamtbetrag"""
        patterns = [
            r"(?:Total|Betrag|Summe|Rechnungsbetrag|Zu zahlen|Gesamtbetrag)[:\s]*(?:CHF|Fr\.?|Franken)?\s*([\d'.,]+)",
            r"(?:CHF|Fr\.?)\s*([\d'.,]+)\s*(?:Total|Summe|Rechnungsbetrag)?",
            r"([\d'.,]+)\s*(?:CHF|Fr\.?|Franken)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                amount_str = amount_str.replace("'", "").replace(",", ".")
                try:
                    return Decimal(amount_str)
                except Exception:
                    continue

        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """Extrahiert das Rechnungsdatum"""
        patterns = [
            (r"(\d{1,2})\.(\d{1,2})\.(\d{4})", "%d.%m.%Y"),
            (r"(\d{1,2})\.(\d{1,2})\.(\d{2})\b", "%d.%m.%y"),
            (r"(\d{4})-(\d{2})-(\d{2})", "%Y-%m-%d"),
        ]

        for pattern, date_format in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    from datetime import datetime
                    date_str = match.group(0)
                    return datetime.strptime(date_str, date_format).date()
                except Exception:
                    continue

        return None

    def _extract_iban(self, text: str) -> Optional[str]:
        """Extrahiert IBAN (Schweizer Format)"""
        pattern = r"CH\s*\d{2}\s*(?:\d{4}\s*){4}\d{1}"
        match = re.search(pattern, text.replace(" ", ""))
        if match:
            return match.group(0).replace(" ", "")
        return None

    def _extract_qr_reference(self, text: str) -> Optional[str]:
        """Extrahiert QR-Referenznummer"""
        pattern = r"\b(\d{26,27})\b"
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return None

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extrahiert Rechnungsnummer"""
        patterns = [
            r"(?:Rechnung(?:s)?(?:nummer|nr\.?)?|Invoice(?:\s+No\.?)?|Nr\.?)[:\s#]*([A-Z0-9-]+)",
            r"(?:Beleg(?:nummer|nr\.?)?)[:\s#]*([A-Z0-9-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_mwst(self, text: str) -> Optional[dict]:
        """Extrahiert MWST-Informationen"""
        satz_pattern = r"(?:MWST|MwSt|Mehrwertsteuer)[:\s]*(\d+(?:[.,]\d+)?)\s*%"
        satz_match = re.search(satz_pattern, text, re.IGNORECASE)

        betrag_pattern = r"(?:MWST|MwSt|Mehrwertsteuer)[:\s]*(?:CHF|Fr\.?)?\s*([\d'.,]+)"
        betrag_match = re.search(betrag_pattern, text, re.IGNORECASE)

        result = {}
        if satz_match:
            result["satz"] = float(satz_match.group(1).replace(",", "."))
        if betrag_match:
            betrag_str = betrag_match.group(1).replace("'", "").replace(",", ".")
            try:
                result["betrag"] = Decimal(betrag_str)
            except Exception:
                pass

        return result if result else None


# Singleton Instance
ocr_service = OCRService()
