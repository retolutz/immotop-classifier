"""
LLM-basierter Rechnungsklassifikator

Verwendet Claude (Anthropic) für:
1. Semantische Analyse des Rechnungstexts
2. Zuordnung zum passenden Konto
3. Konfidenz-Score Berechnung
"""

import json
from typing import Optional
import anthropic

from app.core.config import settings
from app.models.kontenplan import Konto
from app.models.invoice import ClassificationResult, AccountSuggestion, InvoiceData


SYSTEM_PROMPT = """Du bist ein Experte für Schweizer Immobilienbuchhaltung und Kontenplan-Zuordnung.

Deine Aufgabe ist es, Rechnungen dem korrekten Konto aus dem Kontenplan zuzuordnen.

WICHTIGE REGELN:
1. Analysiere den Rechnungstext sorgfältig
2. Berücksichtige den Lieferanten/Kreditor und die Art der Leistung
3. Wähle das SPEZIFISCHSTE passende Konto
4. Gib eine Konfidenz zwischen 0 und 1 an (1 = absolut sicher)
5. Begründe deine Entscheidung kurz
6. Gib 1-2 Alternativen an, falls die Zuordnung nicht eindeutig ist

TYPISCHE ZUORDNUNGEN:
- Heizöl, Gas, Brennstoffe → Konto 4110 oder 4100
- Hauswart, Hauswartung → Konto 4010
- Reinigung, Treppenhausreinigung → Konto 4030
- Strom, Elektrizität → Konto 4120
- Wasser, Abwasser → Konto 4130
- Lift, Aufzug, Förderanlagen → Konto 4050
- Garten, Grünanlagen → Konto 4020
- Versicherung Gebäude → Konto 4200
- Verwaltung, Honorar → Konto 4300

Antworte IMMER im folgenden JSON-Format:
{
    "primary": {
        "konto_seqnr": <int>,
        "konto_nr": "<string>",
        "konto_bez": "<string>",
        "konfidenz": <float 0-1>,
        "begruendung": "<string>"
    },
    "alternativen": [
        {
            "konto_seqnr": <int>,
            "konto_nr": "<string>",
            "konto_bez": "<string>",
            "konfidenz": <float 0-1>,
            "begruendung": "<string>"
        }
    ],
    "extrahierte_daten": {
        "kreditor_name": "<string oder null>",
        "leistungsbeschreibung": "<string>",
        "zeitraum": "<string oder null>"
    }
}"""


class LLMClassifier:
    """Klassifiziert Rechnungen mittels Claude LLM"""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    async def classify(
        self, invoice_data: InvoiceData, konten: list[Konto]
    ) -> ClassificationResult:
        """
        Klassifiziert eine Rechnung und ordnet sie einem Konto zu.

        Args:
            invoice_data: Extrahierte Rechnungsdaten inkl. OCR-Text
            konten: Verfügbare Konten aus dem Immotop2 Kontenplan

        Returns:
            ClassificationResult mit primärem Konto, Alternativen und Konfidenz
        """
        # Kontenplan als Kontext aufbereiten
        konten_context = self._format_konten_for_prompt(konten)

        # User Prompt mit Rechnungsdaten
        user_prompt = f"""Analysiere die folgende Rechnung und ordne sie dem passenden Konto zu.

## KONTENPLAN
{konten_context}

## RECHNUNGSTEXT (OCR)
{invoice_data.raw_text}

## BEREITS EXTRAHIERTE DATEN
- Betrag: {invoice_data.bruttobetrag or 'nicht erkannt'} CHF
- Datum: {invoice_data.rechnungsdatum or 'nicht erkannt'}
- Rechnungsnummer: {invoice_data.rechnungsnummer or 'nicht erkannt'}
- IBAN: {invoice_data.iban or 'nicht erkannt'}

Ordne diese Rechnung dem passenden Konto zu."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Response parsen
            response_text = response.content[0].text
            return self._parse_response(response_text, konten)

        except anthropic.APIError as e:
            # Fallback bei API-Fehler
            return self._fallback_classification(invoice_data, konten, str(e))

    def _format_konten_for_prompt(self, konten: list[Konto]) -> str:
        """Formatiert den Kontenplan für den Prompt"""
        lines = []
        for konto in konten:
            typ = konto.nebenbuch_typ_name
            lines.append(f"- {konto.kontonr}: {konto.bez} [{typ}] (seqnr: {konto.s_seqnr})")
        return "\n".join(lines)

    def _parse_response(
        self, response_text: str, konten: list[Konto]
    ) -> ClassificationResult:
        """Parst die LLM-Antwort in ein ClassificationResult"""
        try:
            # JSON aus der Antwort extrahieren
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)

            primary = AccountSuggestion(
                konto_seqnr=data["primary"]["konto_seqnr"],
                konto_nr=data["primary"]["konto_nr"],
                konto_bez=data["primary"]["konto_bez"],
                konfidenz=min(1.0, max(0.0, data["primary"]["konfidenz"])),
                begruendung=data["primary"]["begruendung"],
            )

            alternativen = [
                AccountSuggestion(
                    konto_seqnr=alt["konto_seqnr"],
                    konto_nr=alt["konto_nr"],
                    konto_bez=alt["konto_bez"],
                    konfidenz=min(1.0, max(0.0, alt["konfidenz"])),
                    begruendung=alt["begruendung"],
                )
                for alt in data.get("alternativen", [])
            ]

            return ClassificationResult(
                primary=primary,
                alternativen=alternativen,
                extrahierte_daten=data.get("extrahierte_daten", {}),
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback wenn Parsing fehlschlägt
            return self._create_uncertain_result(konten, f"Parse-Fehler: {e}")

    def _fallback_classification(
        self, invoice_data: InvoiceData, konten: list[Konto], error: str
    ) -> ClassificationResult:
        """Fallback-Klassifikation bei API-Fehlern"""
        # Einfache Keyword-basierte Zuordnung
        text_lower = invoice_data.raw_text.lower()

        keyword_mapping = {
            "heizöl": "4110",
            "heizoel": "4110",
            "brennstoff": "4110",
            "gas": "4110",
            "hauswart": "4010",
            "reinigung": "4030",
            "putzen": "4030",
            "strom": "4120",
            "elektri": "4120",
            "wasser": "4130",
            "abwasser": "4130",
            "lift": "4050",
            "aufzug": "4050",
            "garten": "4020",
            "grünanlage": "4020",
            "versicherung": "4200",
            "verwaltung": "4300",
            "honorar": "4300",
        }

        matched_konto = None
        for keyword, konto_nr in keyword_mapping.items():
            if keyword in text_lower:
                matched_konto = next(
                    (k for k in konten if k.kontonr == konto_nr), None
                )
                if matched_konto:
                    break

        if matched_konto:
            return ClassificationResult(
                primary=AccountSuggestion(
                    konto_seqnr=matched_konto.s_seqnr,
                    konto_nr=matched_konto.kontonr,
                    konto_bez=matched_konto.bez,
                    konfidenz=0.5,
                    begruendung=f"Fallback-Klassifikation (Keyword-Match). LLM-Fehler: {error}",
                ),
                alternativen=[],
                extrahierte_daten={},
            )

        return self._create_uncertain_result(konten, error)

    def _create_uncertain_result(
        self, konten: list[Konto], reason: str
    ) -> ClassificationResult:
        """Erstellt ein unsicheres Ergebnis wenn keine Zuordnung möglich"""
        # Nimm das allgemeinste Konto (Unterhalt und Reparaturen)
        default_konto = next(
            (k for k in konten if k.kontonr == "4000"),
            konten[0] if konten else None,
        )

        if not default_konto:
            raise ValueError("Kein Konto verfügbar")

        return ClassificationResult(
            primary=AccountSuggestion(
                konto_seqnr=default_konto.s_seqnr,
                konto_nr=default_konto.kontonr,
                konto_bez=default_konto.bez,
                konfidenz=0.1,
                begruendung=f"Unsichere Zuordnung - bitte manuell prüfen. Grund: {reason}",
            ),
            alternativen=[],
            extrahierte_daten={},
        )


# Singleton Instance
llm_classifier = LLMClassifier()
