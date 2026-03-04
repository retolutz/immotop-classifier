"""
OCR Service für Schweizer Rechnungen

Unterstützt:
- PDF (Text-Extraktion via PyPDF2)
- Swiss QR-Bill (automatische Erkennung und Parsing)
- Bilder (benötigt lokales Tesseract - auf Azure deaktiviert)
"""

import io
import re
from typing import Optional, Tuple
from datetime import date
from decimal import Decimal
from pathlib import Path

from PyPDF2 import PdfReader

from app.models.invoice import InvoiceData
from app.services.qr_service import qr_service, SwissQRData

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
    ) -> Tuple[InvoiceData, Optional[SwissQRData]]:
        """
        Extrahiert Text und Daten aus einer Datei.

        Returns:
            Tuple von (InvoiceData, Optional[SwissQRData])
        """
        extension = Path(filename).suffix.lower()
        qr_data = None

        if extension == ".pdf":
            raw_text = await self._extract_from_pdf(file_bytes)
            # Versuche QR-Code zu extrahieren
            qr_data = await qr_service.extract_from_pdf(file_bytes)
        elif extension in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            raw_text = await self._extract_from_image(file_bytes)
            # Versuche QR-Code aus Bild zu extrahieren
            qr_data = await qr_service.extract_from_image(file_bytes)
        else:
            raise ValueError(f"Nicht unterstütztes Format: {extension}")

        # Strukturierte Daten extrahieren
        invoice_data = self._parse_invoice_text(raw_text)

        # QR-Daten haben Priorität (100% genau)
        if qr_data:
            invoice_data = self._merge_qr_data(invoice_data, qr_data)

        return invoice_data, qr_data

    def _merge_qr_data(self, invoice_data: InvoiceData, qr_data: SwissQRData) -> InvoiceData:
        """Merged QR-Daten in InvoiceData (QR hat Priorität)"""

        # Betrag aus QR (100% genau)
        if qr_data.amount:
            invoice_data.bruttobetrag = qr_data.amount

        # IBAN aus QR
        if qr_data.iban:
            invoice_data.iban = qr_data.iban

        # Kreditor aus QR
        if qr_data.creditor_name:
            invoice_data.kreditor_name = qr_data.creditor_name

        if qr_data.creditor_street or qr_data.creditor_city:
            parts = []
            if qr_data.creditor_street:
                parts.append(qr_data.creditor_street)
            if qr_data.creditor_building:
                parts.append(qr_data.creditor_building)
            if qr_data.creditor_postcode and qr_data.creditor_city:
                parts.append(f"{qr_data.creditor_postcode} {qr_data.creditor_city}")
            invoice_data.kreditor_adresse = ", ".join(parts)

        # Referenz als Rechnungsnummer
        if qr_data.reference:
            invoice_data.qr_referenz = qr_data.reference
            if not invoice_data.rechnungsnummer:
                invoice_data.rechnungsnummer = qr_data.reference

        # Währung
        if qr_data.currency:
            invoice_data.waehrung = qr_data.currency

        # Unstrukturierte Mitteilung als Beschreibung
        if qr_data.unstructured_message:
            invoice_data.beschreibung = qr_data.unstructured_message

        return invoice_data

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
        """Extrahiert den Gesamtbetrag - sucht spezifisch nach Rechnungstotal"""
        # Priorität 1: Spezifische Total-Bezeichnungen (Schweizer Rechnungen)
        priority_patterns = [
            r"Rechnungstotal[:\s]*(?:CHF|Fr\.?)?\s*([\d'`.,]+)",
            r"Total\s+(?:CHF|Fr\.?)\s*([\d'`.,]+)",
            r"Gesamtbetrag[:\s]*(?:CHF|Fr\.?)?\s*([\d'`.,]+)",
            r"Zu\s+zahlen[:\s]*(?:CHF|Fr\.?)?\s*([\d'`.,]+)",
            r"Endbetrag[:\s]*(?:CHF|Fr\.?)?\s*([\d'`.,]+)",
        ]

        for pattern in priority_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                # Schweizer Formate: 1'949.75 oder 1`949.75
                amount_str = amount_str.replace("'", "").replace("`", "").replace(",", ".")
                try:
                    amount = Decimal(amount_str)
                    if amount > 0:
                        return amount
                except Exception:
                    continue

        # Priorität 2: Grösster CHF-Betrag finden (oft der Totalbetrag)
        all_amounts = []
        amount_pattern = r"(?:CHF|Fr\.?)\s*([\d'`.,]+)"
        for match in re.finditer(amount_pattern, text, re.IGNORECASE):
            amount_str = match.group(1)
            amount_str = amount_str.replace("'", "").replace("`", "").replace(",", ".")
            try:
                amount = Decimal(amount_str)
                if amount > 0:
                    all_amounts.append(amount)
            except Exception:
                continue

        if all_amounts:
            # Rückgabe des grössten Betrags (typischerweise der Gesamtbetrag)
            return max(all_amounts)

        return None

    def _extract_date(self, text: str) -> Optional[date]:
        """Extrahiert das Rechnungsdatum"""
        from datetime import datetime

        # Zuerst nach "Datum:" oder "Rechnungsdatum:" suchen
        date_context_patterns = [
            r"(?:Datum|Rechnungsdatum)[:\s]+(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})",
            r"(?:Datum|Rechnungsdatum)[:\s]+(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{2})\b",
        ]

        for pattern in date_context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    day, month, year = match.groups()
                    if len(year) == 2:
                        year = "20" + year
                    return datetime(int(year), int(month), int(day)).date()
                except Exception:
                    continue

        # Fallback: Allgemeine Datumsmuster (mit optionalen Leerzeichen)
        patterns = [
            r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})",  # 01. 07.2020 oder 01.07.2020
            r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{2})\b",  # 01.07.20
            r"(\d{4})-(\d{2})-(\d{2})",  # 2020-07-01
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    groups = match.groups()
                    if "-" in match.group(0):  # ISO format
                        year, month, day = groups
                    else:
                        day, month, year = groups
                        if len(year) == 2:
                            year = "20" + year
                    return datetime(int(year), int(month), int(day)).date()
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
            r"Rechnung\s+Nr\.?\s*[:\s]*([A-Za-z0-9\-/]+)",  # "Rechnung Nr. 10201409"
            r"Rechnungs?(?:nummer|nr\.?)\s*[:\s#]*([A-Za-z0-9\-/]+)",
            r"Invoice\s*(?:No\.?|Number)?\s*[:\s#]*([A-Za-z0-9\-/]+)",
            r"Beleg(?:nummer|nr\.?)\s*[:\s#]*([A-Za-z0-9\-/]+)",
            r"Nr\.?\s*[:\s]*(\d{6,})",  # "Nr. 10201409" (mindestens 6 Ziffern)
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                # Nur zurückgeben wenn es substantiell ist (nicht nur "Nr")
                if len(result) >= 3 and result.lower() not in ["nr", "nr."]:
                    return result

        return None

    def _extract_mwst(self, text: str) -> Optional[dict]:
        """Extrahiert MWST-Informationen aus Schweizer Rechnungen"""
        result = {}

        # MwSt-Satz extrahieren (z.B. "MwSt.  7.7 %" oder "7.7% MwSt")
        satz_patterns = [
            r"(?:MWST|MwSt\.?|Mehrwertsteuer)\s*[:\s]*(\d+(?:[.,]\d+)?)\s*%",
            r"(\d+(?:[.,]\d+)?)\s*%\s*(?:MWST|MwSt\.?)",
        ]
        for pattern in satz_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["satz"] = float(match.group(1).replace(",", "."))
                break

        # MwSt-Betrag extrahieren - verschiedene Muster
        betrag_patterns = [
            # "MwSt. Betrag  CHF 139.40" - Betrag ist required
            r"(?:MWST|MwSt\.?)\s*Betrag\s*[:\s]*(?:CHF|Fr\.?)?\s*([\d'`.,]+)",
            # "MwSt CHF 139.40" - CHF direkt nach MwSt
            r"(?:MWST|MwSt\.?)\s*(?:CHF|Fr\.?)\s*([\d'`.,]+)",
            # "Steuer/TVA CHF 139.40"
            r"(?:Steuer|Taxe|TVA)\s*[:\s]*(?:CHF|Fr\.?)?\s*([\d'`.,]+)",
        ]
        for pattern in betrag_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                betrag_str = match.group(1).replace("'", "").replace("`", "").replace(",", ".")
                try:
                    betrag = Decimal(betrag_str)
                    # Nur plausible Beträge akzeptieren (nicht der Satz!)
                    if betrag > 1 and betrag < 100000:
                        result["betrag"] = betrag
                        break
                except Exception:
                    continue

        return result if result else None


# Singleton Instance
ocr_service = OCRService()
