#!/usr/bin/env python3
"""
API-Tests für die Rechnungsklassifizierung
Testet echte PDFs und generiert Testberichte
"""

import httpx
import asyncio
import json
from pathlib import Path
from datetime import datetime

API_URL = "https://immotop-classifier.onrender.com/api"

# Erwartete Klassifikationen für echte PDFs
EXPECTED_RESULTS = {
    "rechnung-qr-code.pdf": {
        "expected_konto": "4020",
        "expected_name": "Gartenunterhalt",
        "reason": "Gartenarbeiten und Entsorgung Schnittmaterial"
    },
    "handwerker-at.pdf": {
        "expected_konto": "4000",
        "expected_name": "Unterhalt und Reparaturen",
        "reason": "Allgemeine Handwerkerrechnung"
    },
    "handwerker-de.pdf": {
        "expected_konto": "4000",
        "expected_name": "Unterhalt und Reparaturen",
        "reason": "Malerarbeiten (Handwerker)"
    },
    "ihk-muster.pdf": {
        "expected_konto": "4000",
        "expected_name": "Unterhalt und Reparaturen",
        "reason": "Allgemeine Geschäftsrechnung"
    },
}


async def test_pdf(filepath: Path) -> dict:
    """Testet ein einzelnes PDF über die API"""
    print(f"\nTeste: {filepath.name}...")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(filepath, "rb") as f:
                files = {"file": (filepath.name, f, "application/pdf")}
                response = await client.post(
                    f"{API_URL}/upload",
                    files=files
                )

            if response.status_code != 200:
                return {
                    "filename": filepath.name,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }

            data = response.json()

            classification = data.get("classification", {})
            primary = classification.get("primary", {})
            invoice_data = data.get("invoice_data", {})
            extrahierte_daten = classification.get("extrahierte_daten", {})

            return {
                "filename": filepath.name,
                "success": True,
                "classified_konto": primary.get("konto_nr"),
                "classified_name": primary.get("konto_bez"),
                "confidence": primary.get("konfidenz"),
                "reason": primary.get("begruendung"),
                "extracted_amount": invoice_data.get("bruttobetrag"),
                "extracted_date": invoice_data.get("rechnungsdatum"),
                "extracted_kreditor": extrahierte_daten.get("kreditor_name"),
                "extracted_description": extrahierte_daten.get("leistungsbeschreibung"),
                "alternatives": [
                    {
                        "konto": alt.get("konto_nr"),
                        "name": alt.get("konto_bez"),
                        "confidence": alt.get("konfidenz")
                    }
                    for alt in classification.get("alternativen", [])
                ]
            }

    except Exception as e:
        return {
            "filename": filepath.name,
            "success": False,
            "error": str(e)
        }


def evaluate_result(result: dict, expected: dict) -> dict:
    """Bewertet ein Testergebnis"""
    if not result.get("success"):
        return {
            "correct": False,
            "reason": f"Test fehlgeschlagen: {result.get('error')}"
        }

    classified = result.get("classified_konto")
    expected_konto = expected.get("expected_konto")

    is_correct = classified == expected_konto

    # Auch prüfen ob in Alternativen
    in_alternatives = False
    for alt in result.get("alternatives", []):
        if alt.get("konto") == expected_konto:
            in_alternatives = True
            break

    return {
        "correct": is_correct,
        "in_alternatives": in_alternatives,
        "classified": classified,
        "expected": expected_konto,
        "confidence": result.get("confidence"),
    }


async def run_tests():
    """Führt alle Tests durch"""
    print("=" * 70)
    print("QUALITÄTSTEST: Rechnungsklassifizierung API")
    print(f"Zeitpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API: {API_URL}")
    print("=" * 70)

    # Finde alle PDFs
    test_dir = Path(__file__).parent
    pdf_files = list(test_dir.glob("*.pdf"))

    # Filtere ungültige PDFs (zu klein)
    valid_pdfs = [p for p in pdf_files if p.stat().st_size > 1000]

    print(f"\nGefundene gültige PDFs: {len(valid_pdfs)}")
    for pdf in valid_pdfs:
        print(f"  - {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")

    # Teste alle PDFs
    results = []
    for pdf_path in valid_pdfs:
        result = await test_pdf(pdf_path)
        results.append(result)

        # Kurze Pause zwischen Requests
        await asyncio.sleep(2)

    # Auswertung
    print("\n" + "=" * 70)
    print("TESTERGEBNISSE")
    print("=" * 70)

    correct_count = 0
    total_count = len(results)

    for result in results:
        filename = result.get("filename")
        expected = EXPECTED_RESULTS.get(filename, {})
        evaluation = evaluate_result(result, expected)

        print(f"\n📄 {filename}")
        print("-" * 50)

        if not result.get("success"):
            print(f"  ❌ FEHLER: {result.get('error')}")
            continue

        classified = result.get("classified_konto")
        classified_name = result.get("classified_name")
        confidence = result.get("confidence", 0) * 100
        expected_konto = expected.get("expected_konto", "N/A")
        expected_name = expected.get("expected_name", "N/A")

        if evaluation.get("correct"):
            print(f"  ✅ KORREKT")
            correct_count += 1
        elif evaluation.get("in_alternatives"):
            print(f"  ⚠️  TEILWEISE (in Alternativen)")
            correct_count += 0.5
        else:
            print(f"  ❌ FALSCH")

        print(f"  Klassifiziert: {classified} - {classified_name} ({confidence:.0f}%)")
        print(f"  Erwartet:      {expected_konto} - {expected_name}")
        print(f"  Begründung:    {result.get('reason', 'N/A')[:80]}...")

        # Extrahierte Daten
        print(f"\n  Extrahierte Daten:")
        print(f"    Betrag:    CHF {result.get('extracted_amount', 'N/A')}")
        print(f"    Datum:     {result.get('extracted_date', 'N/A')}")
        print(f"    Kreditor:  {result.get('extracted_kreditor', 'N/A')}")
        print(f"    Leistung:  {result.get('extracted_description', 'N/A')}")

        # Alternativen
        if result.get("alternatives"):
            print(f"\n  Alternativen:")
            for alt in result.get("alternatives", [])[:2]:
                print(f"    - {alt['konto']} {alt['name']} ({alt['confidence']*100:.0f}%)")

    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)

    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

    print(f"\nGetestet:        {total_count} PDFs")
    print(f"Korrekt:         {correct_count:.1f}")
    print(f"Genauigkeit:     {accuracy:.1f}%")

    # Bewertung
    print(f"\nBewertung:")
    if accuracy >= 90:
        print("  🌟 Ausgezeichnet - Produktionsreif")
    elif accuracy >= 75:
        print("  ✅ Gut - Kleine Verbesserungen nötig")
    elif accuracy >= 50:
        print("  ⚠️  Mittel - Signifikante Verbesserungen nötig")
    else:
        print("  ❌ Ungenügend - Grundlegende Überarbeitung nötig")

    # Speichere detaillierte Ergebnisse
    report = {
        "timestamp": datetime.now().isoformat(),
        "api_url": API_URL,
        "total_tests": total_count,
        "correct": correct_count,
        "accuracy_percent": accuracy,
        "results": results,
    }

    report_path = test_dir / "test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    print(f"\nDetailbericht gespeichert: {report_path}")

    return report


if __name__ == "__main__":
    asyncio.run(run_tests())
