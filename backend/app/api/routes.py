"""
API Routes für den Invoice Classifier
"""

import uuid
import base64
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response

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
from app.services.qr_service import qr_service

router = APIRouter()

# In-Memory Cache für hochgeladene Rechnungen (in Produktion: Redis/DB)
invoice_cache: dict[str, dict] = {}


@router.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "service": "immotop-invoice-classifier",
        "qr_enabled": qr_service.is_available(),
    }


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

        # OCR durchführen (inkl. QR-Code Extraktion)
        invoice_data, qr_data = await ocr_service.extract_from_bytes(file_bytes, file.filename)

        # Konten laden für Klassifikation
        konten = await immotop_client.get_konten()

        # LLM-Klassifikation
        classification = await llm_classifier.classify(invoice_data, konten)

        # Merge LLM-extrahierte Daten zurück in invoice_data
        # (LLM ist oft besser bei Datumsextraktion etc.)
        if classification.extrahierte_daten:
            ext = classification.extrahierte_daten
            # Datum übernehmen wenn nicht schon vorhanden
            if ext.get("rechnungsdatum") and not invoice_data.rechnungsdatum:
                try:
                    from datetime import datetime
                    date_str = ext["rechnungsdatum"]
                    if isinstance(date_str, str):
                        invoice_data.rechnungsdatum = datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    pass
            # Kreditor-Name falls nicht vorhanden
            if ext.get("kreditor_name") and not invoice_data.kreditor_name:
                invoice_data.kreditor_name = ext["kreditor_name"]
            # Betrag als Fallback
            if ext.get("bruttobetrag") and not invoice_data.bruttobetrag:
                from decimal import Decimal
                invoice_data.bruttobetrag = Decimal(str(ext["bruttobetrag"]))
            # Leistungsbeschreibung
            if ext.get("leistungsbeschreibung") and not invoice_data.beschreibung:
                invoice_data.beschreibung = ext["leistungsbeschreibung"]

        # Ergebnis cachen
        invoice_id = str(uuid.uuid4())
        invoice_cache[invoice_id] = {
            "filename": file.filename,
            "invoice_data": invoice_data,
            "classification": classification,
            "file_bytes": file_bytes,
            "qr_data": qr_data,
            "has_qr": qr_data is not None,
        }

        # Response mit QR-Info erweitern
        response = InvoiceUploadResponse(
            id=invoice_id,
            filename=file.filename,
            invoice_data=invoice_data,
            classification=classification,
        )

        return response

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


@router.get("/invoice/{invoice_id}/preview")
async def get_invoice_preview(invoice_id: str):
    """
    Gibt die PDF/Bild-Datei als Base64 zurück für die Vorschau im Browser.
    """
    if invoice_id not in invoice_cache:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")

    cached = invoice_cache[invoice_id]
    file_bytes = cached.get("file_bytes")
    filename = cached.get("filename", "document")

    if not file_bytes:
        raise HTTPException(status_code=404, detail="Datei nicht im Cache")

    # MIME-Type bestimmen
    ext = filename.lower().split(".")[-1] if "." in filename else "pdf"
    mime_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
    }
    mime_type = mime_types.get(ext, "application/octet-stream")

    # Base64 encodieren
    base64_data = base64.b64encode(file_bytes).decode("utf-8")

    return {
        "filename": filename,
        "mime_type": mime_type,
        "data": base64_data,
        "has_qr": cached.get("has_qr", False),
    }


@router.get("/invoice/{invoice_id}/file")
async def get_invoice_file(invoice_id: str):
    """
    Gibt die Original-Datei direkt zurück (für Download oder iframe).
    """
    if invoice_id not in invoice_cache:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")

    cached = invoice_cache[invoice_id]
    file_bytes = cached.get("file_bytes")
    filename = cached.get("filename", "document.pdf")

    if not file_bytes:
        raise HTTPException(status_code=404, detail="Datei nicht im Cache")

    # MIME-Type bestimmen
    ext = filename.lower().split(".")[-1] if "." in filename else "pdf"
    mime_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "bmp": "image/bmp",
    }
    mime_type = mime_types.get(ext, "application/octet-stream")

    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        }
    )
