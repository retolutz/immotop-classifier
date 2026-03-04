from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal


class AccountSuggestion(BaseModel):
    """Ein Kontovorschlag mit Konfidenz"""

    konto_seqnr: int
    konto_nr: str
    konto_bez: str
    konfidenz: float = Field(ge=0.0, le=1.0, description="Konfidenz 0-1")
    begruendung: str


class ClassificationResult(BaseModel):
    """Ergebnis der LLM-Klassifikation"""

    primary: AccountSuggestion
    alternativen: list[AccountSuggestion] = []
    extrahierte_daten: dict = {}


class InvoiceData(BaseModel):
    """Extrahierte Rechnungsdaten"""

    raw_text: str
    kreditor_name: Optional[str] = None
    kreditor_adresse: Optional[str] = None
    rechnungsnummer: Optional[str] = None
    rechnungsdatum: Optional[date] = None
    faelligkeitsdatum: Optional[date] = None
    bruttobetrag: Optional[Decimal] = None
    nettobetrag: Optional[Decimal] = None
    mwst_betrag: Optional[Decimal] = None
    mwst_satz: Optional[float] = None
    waehrung: str = "CHF"
    iban: Optional[str] = None
    qr_referenz: Optional[str] = None
    beschreibung: Optional[str] = None


class InvoiceUploadResponse(BaseModel):
    """Antwort nach Upload einer Rechnung"""

    id: str
    filename: str
    invoice_data: InvoiceData
    classification: ClassificationResult
    preview_url: Optional[str] = None


class BelegPosten(BaseModel):
    """Einzelne Buchungsposition gemäss Immotop2 DMS-Schnittstelle"""

    konto_seqnr: int
    kostenstelle_seqnr: Optional[int] = None
    bruttobetrag: Decimal  # betragbrutto
    betrag_exkl_mwst: Optional[Decimal] = None  # betragexklmwst
    betrag_mwst: Optional[Decimal] = None  # betragmwstvoll
    mwst_satz: Optional[float] = None  # mwstsatz (z.B. 7.7)
    mwst_code_seqnr: Optional[int] = None  # mwstcode_seqnr
    buchungstext: str


class ImmotopSubmitRequest(BaseModel):
    """Request zum Senden an Immotop2 gemäss DMS-Schnittstelle"""

    invoice_id: str
    mandant_seqnr: int
    kreditor_seqnr: Optional[int] = None
    neuer_kreditor: Optional[dict] = None  # Falls neuer Kreditor erstellt werden muss
    belegdatum: date
    faelligkeitsdatum: Optional[date] = None
    bruttobetrag: Decimal
    buchungstext: str
    positionen: list[BelegPosten]
    # Zusätzliche Felder gemäss DmsBeleg
    rechnungsnummer: Optional[str] = None  # rechnungnummer
    esrreferenznummer: Optional[str] = None  # QR-Referenz
    qrcodepayload: Optional[str] = None  # Ganzer QR-Code Inhalt
    kreditor_iban: Optional[str] = None  # kreditorzahlstellekontodetail


class ImmotopSubmitResponse(BaseModel):
    """Antwort von Immotop2 nach Beleg-Erstellung"""

    success: bool
    import_seqnr: Optional[int] = None
    beleg_seqnr: Optional[int] = None
    message: str
    immotop_url: Optional[str] = None
