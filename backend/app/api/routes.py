"""
API Routes für den Invoice Classifier
"""

import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.models import (
    InvoiceUploadResponse,
    ImmotopSubmitRequest,
    ImmotopSubmitResponse,
    Konto,
    Kreditor,
    BelegPosten,
)
from app.services.immotop_client import immotop_client
from app.services.ocr_service import ocr_service
from app.services.llm_classifier import llm_classifier

router = APIRouter()

# In-Memory Cache für hochgeladene Rechnungen (in Produktion: Redis/DB)
invoice_cache: dict[str, dict] = {}


@router.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {"status": "healthy", "service": "immotop-invoice-classifier"}


@router.get("/konten", response_model=list[Konto])
async def get_konten(mandant_seqnr: int = 1):
    """Lädt alle verfügbaren Konten aus Immotop2"""
    try:
        konten = await immotop_client.get_konten(mandant_seqnr)
        return konten
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Konten: {e}")


@router.get("/kreditoren", response_model=list[Kreditor])
async def get_kreditoren(mandant_seqnr: int = 1):
    """Lädt alle verfügbaren Kreditoren aus Immotop2"""
    try:
        kreditoren = await immotop_client.get_kreditoren(mandant_seqnr)
        return kreditoren
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Kreditoren: {e}")


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(file: UploadFile = File(...)):
    """
    Lädt eine Rechnung hoch, extrahiert Daten via OCR und klassifiziert sie.

    Unterstützte Formate: PDF, PNG, JPG, JPEG, TIFF, BMP
    """
    # Dateiformat validieren
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Nicht unterstütztes Format: {file_ext}. Erlaubt: {', '.join(allowed_extensions)}",
        )

    try:
        # Datei lesen
        file_bytes = await file.read()

        # OCR durchführen
        invoice_data = await ocr_service.extract_from_bytes(file_bytes, file.filename)

        # Konten laden für Klassifikation
        konten = await immotop_client.get_konten()

        # LLM-Klassifikation
        classification = await llm_classifier.classify(invoice_data, konten)

        # Ergebnis cachen
        invoice_id = str(uuid.uuid4())
        invoice_cache[invoice_id] = {
            "filename": file.filename,
            "invoice_data": invoice_data,
            "classification": classification,
            "file_bytes": file_bytes,
        }

        return InvoiceUploadResponse(
            id=invoice_id,
            filename=file.filename,
            invoice_data=invoice_data,
            classification=classification,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verarbeitungsfehler: {str(e)}")


@router.post("/submit", response_model=ImmotopSubmitResponse)
async def submit_to_immotop(request: ImmotopSubmitRequest):
    """
    Sendet eine klassifizierte Rechnung an Immotop2.

    Die Rechnung muss zuvor über /upload hochgeladen worden sein.
    """
    # Rechnung aus Cache holen
    if request.invoice_id not in invoice_cache:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden. Bitte erneut hochladen.")

    try:
        # An Immotop2 senden
        response = await immotop_client.submit_beleg(
            mandant_seqnr=request.mandant_seqnr,
            kreditor_seqnr=request.kreditor_seqnr,
            belegdatum=request.belegdatum,
            bruttobetrag=request.bruttobetrag,
            buchungstext=request.buchungstext,
            positionen=request.positionen,
            faelligkeitsdatum=request.faelligkeitsdatum,
        )

        # Bei Erfolg aus Cache entfernen
        if response.success:
            del invoice_cache[request.invoice_id]

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Senden an Immotop2: {str(e)}")


@router.get("/invoice/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Ruft eine gecachte Rechnung ab"""
    if invoice_id not in invoice_cache:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")

    cached = invoice_cache[invoice_id]
    return {
        "id": invoice_id,
        "filename": cached["filename"],
        "invoice_data": cached["invoice_data"],
        "classification": cached["classification"],
    }


@router.delete("/invoice/{invoice_id}")
async def delete_invoice(invoice_id: str):
    """Löscht eine gecachte Rechnung"""
    if invoice_id not in invoice_cache:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")

    del invoice_cache[invoice_id]
    return {"message": "Rechnung gelöscht", "id": invoice_id}
