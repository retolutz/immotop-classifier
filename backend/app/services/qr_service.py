"""
Swiss QR-Bill Decoder Service

Extrahiert Zahlungsinformationen aus Schweizer QR-Rechnungen.
Das Swiss QR-Bill Format ist standardisiert (ISO 20022).
"""

import io
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import date

# Optionale Imports - Fallback wenn nicht verfügbar
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pyzbar import pyzbar
    from PIL import Image
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False


@dataclass
class SwissQRData:
    """Daten aus einem Swiss QR-Bill"""
    # Zahlungsempfänger
    iban: Optional[str] = None
    creditor_name: Optional[str] = None
    creditor_street: Optional[str] = None
    creditor_building: Optional[str] = None
    creditor_postcode: Optional[str] = None
    creditor_city: Optional[str] = None
    creditor_country: Optional[str] = None

    # Betrag
    amount: Optional[Decimal] = None
    currency: str = "CHF"

    # Schuldner (optional)
    debtor_name: Optional[str] = None
    debtor_street: Optional[str] = None
    debtor_postcode: Optional[str] = None
    debtor_city: Optional[str] = None

    # Referenz
    reference_type: Optional[str] = None  # QRR, SCOR, NON
    reference: Optional[str] = None

    # Zusätzliche Infos
    unstructured_message: Optional[str] = None
    billing_info: Optional[str] = None

    # Meta
    raw_qr_data: Optional[str] = None


class SwissQRService:
    """Service zum Dekodieren von Swiss QR-Bills"""

    def __init__(self):
        self.available = PYMUPDF_AVAILABLE and PYZBAR_AVAILABLE

    async def extract_from_pdf(self, pdf_bytes: bytes) -> Optional[SwissQRData]:
        """
        Extrahiert QR-Code Daten aus einem PDF.

        Args:
            pdf_bytes: PDF als Bytes

        Returns:
            SwissQRData wenn QR-Code gefunden, sonst None
        """
        if not self.available:
            return None

        try:
            # PDF öffnen
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            # Durch alle Seiten iterieren (QR meist auf letzter Seite)
            for page_num in range(len(doc)):
                page = doc[page_num]

                # Seite als Bild rendern (höhere Auflösung für bessere QR-Erkennung)
                mat = fitz.Matrix(2.0, 2.0)  # 2x Zoom
                pix = page.get_pixmap(matrix=mat)

                # Zu PIL Image konvertieren
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # QR-Codes suchen
                qr_codes = pyzbar.decode(img)

                for qr in qr_codes:
                    if qr.type == 'QRCODE':
                        qr_data = qr.data.decode('utf-8')

                        # Prüfen ob es ein Swiss QR-Bill ist
                        if qr_data.startswith('SPC'):
                            doc.close()
                            return self._parse_swiss_qr(qr_data)

            doc.close()
            return None

        except Exception as e:
            print(f"QR extraction error: {e}")
            return None

    async def extract_from_image(self, image_bytes: bytes) -> Optional[SwissQRData]:
        """Extrahiert QR-Code aus einem Bild"""
        if not PYZBAR_AVAILABLE:
            return None

        try:
            img = Image.open(io.BytesIO(image_bytes))
            qr_codes = pyzbar.decode(img)

            for qr in qr_codes:
                if qr.type == 'QRCODE':
                    qr_data = qr.data.decode('utf-8')
                    if qr_data.startswith('SPC'):
                        return self._parse_swiss_qr(qr_data)

            return None
        except Exception as e:
            print(f"QR image extraction error: {e}")
            return None

    def _parse_swiss_qr(self, qr_data: str) -> SwissQRData:
        """
        Parst den Inhalt eines Swiss QR-Bills.

        Format (Zeilen durch \n getrennt):
        0: SPC (Header)
        1: 0200 (Version)
        2: 1 (Coding - UTF-8)
        3: IBAN
        4: Adresstyp Kreditor (S=strukturiert, K=kombiniert)
        5: Name Kreditor
        6: Strasse oder Adresszeile 1
        7: Hausnummer oder Adresszeile 2
        8: PLZ
        9: Ort
        10: Land (2-Letter ISO)
        11-17: Ultimate Creditor (meist leer)
        18: Betrag
        19: Währung
        20: Adresstyp Schuldner
        21-26: Schuldner Adresse
        27: Referenztyp (QRR, SCOR, NON)
        28: Referenz
        29: Unstrukturierte Mitteilung
        30: Trailer (EPD)
        31: Rechnungsinformationen
        """
        result = SwissQRData(raw_qr_data=qr_data)

        lines = qr_data.split('\n')

        try:
            # Header prüfen
            if len(lines) < 3 or lines[0] != 'SPC':
                return result

            # IBAN (Zeile 3)
            if len(lines) > 3:
                result.iban = lines[3].strip() if lines[3].strip() else None

            # Kreditor Adresse (Zeilen 4-10)
            if len(lines) > 5:
                result.creditor_name = lines[5].strip() if lines[5].strip() else None
            if len(lines) > 6:
                result.creditor_street = lines[6].strip() if lines[6].strip() else None
            if len(lines) > 7:
                result.creditor_building = lines[7].strip() if lines[7].strip() else None
            if len(lines) > 8:
                result.creditor_postcode = lines[8].strip() if lines[8].strip() else None
            if len(lines) > 9:
                result.creditor_city = lines[9].strip() if lines[9].strip() else None
            if len(lines) > 10:
                result.creditor_country = lines[10].strip() if lines[10].strip() else None

            # Betrag (Zeile 18)
            if len(lines) > 18 and lines[18].strip():
                try:
                    result.amount = Decimal(lines[18].strip())
                except:
                    pass

            # Währung (Zeile 19)
            if len(lines) > 19 and lines[19].strip():
                result.currency = lines[19].strip()

            # Schuldner (Zeilen 20-26)
            if len(lines) > 21 and lines[21].strip():
                result.debtor_name = lines[21].strip()
            if len(lines) > 22 and lines[22].strip():
                result.debtor_street = lines[22].strip()
            if len(lines) > 24 and lines[24].strip():
                result.debtor_postcode = lines[24].strip()
            if len(lines) > 25 and lines[25].strip():
                result.debtor_city = lines[25].strip()

            # Referenz (Zeilen 27-28)
            if len(lines) > 27:
                result.reference_type = lines[27].strip() if lines[27].strip() else None
            if len(lines) > 28:
                result.reference = lines[28].strip() if lines[28].strip() else None

            # Unstrukturierte Mitteilung (Zeile 29)
            if len(lines) > 29:
                result.unstructured_message = lines[29].strip() if lines[29].strip() else None

            # Rechnungsinformationen (Zeile 31)
            if len(lines) > 31:
                result.billing_info = lines[31].strip() if lines[31].strip() else None

        except Exception as e:
            print(f"Swiss QR parse error: {e}")

        return result

    def is_available(self) -> bool:
        """Prüft ob QR-Erkennung verfügbar ist"""
        return self.available


# Singleton
qr_service = SwissQRService()
