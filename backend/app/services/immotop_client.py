"""
Immotop2 REST API Client

Basierend auf: https://github.com/wwimmo/immotop2-dms-schnittstelle
"""

import httpx
from typing import Optional
from datetime import date
from decimal import Decimal
import base64
import json

from app.core.config import settings
from app.models.kontenplan import Konto, Kreditor
from app.models.invoice import ImmotopSubmitResponse, BelegPosten


class ImmotopClient:
    """Client für die Immotop2 REST API"""

    def __init__(self):
        self.base_url = settings.immotop_api_url
        self.mock_mode = settings.immotop_mock_mode

        # Basic Auth Header
        credentials = f"{settings.immotop_username}:{settings.immotop_password}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        self.headers = {
            "Authorization": f"Basic {auth_header}",
            "Version": "1.0",
            "Content-Type": "text/plain",
        }

    async def get_konten(self, mandant_seqnr: int = 1) -> list[Konto]:
        """Lädt alle Konten für einen Mandanten"""
        if self.mock_mode:
            return self._get_mock_konten()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/GetDmsKonto",
                headers=self.headers,
                params={"mandant_seqnr": mandant_seqnr},
            )
            response.raise_for_status()
            data = response.json()
            return [Konto(**item) for item in data]

    async def get_kreditoren(self, mandant_seqnr: int = 1) -> list[Kreditor]:
        """Lädt alle Kreditoren für einen Mandanten"""
        if self.mock_mode:
            return self._get_mock_kreditoren()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/GetDmsKreditor",
                headers=self.headers,
                params={"mandant_seqnr": mandant_seqnr},
            )
            response.raise_for_status()
            data = response.json()
            return [Kreditor(**item) for item in data]

    async def submit_beleg(
        self,
        mandant_seqnr: int,
        kreditor_seqnr: int,
        belegdatum: date,
        bruttobetrag: Decimal,
        buchungstext: str,
        positionen: list[BelegPosten],
        faelligkeitsdatum: Optional[date] = None,
    ) -> ImmotopSubmitResponse:
        """Sendet einen Beleg an Immotop2 via SaveDmsImport"""
        if self.mock_mode:
            return self._mock_submit_beleg(mandant_seqnr, bruttobetrag)

        # Beleg-Positionen aufbereiten
        beleg_posten_list = [
            {
                "konto_seqnr": pos.konto_seqnr,
                "kostenstelle_seqnr": pos.kostenstelle_seqnr,
                "bruttobetrag": float(pos.bruttobetrag),
                "buchungstext": pos.buchungstext,
            }
            for pos in positionen
        ]

        payload = {
            "mandant_seqnr": mandant_seqnr,
            "kreditor_seqnr": kreditor_seqnr,
            "belegdatum": belegdatum.isoformat(),
            "bruttobetrag": float(bruttobetrag),
            "buchungstext": buchungstext,
            "BelegPostenList": beleg_posten_list,
        }

        if faelligkeitsdatum:
            payload["faelligkeitsdatum"] = faelligkeitsdatum.isoformat()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/SaveDmsImport",
                headers=self.headers,
                content=json.dumps(payload),
            )

            if response.status_code == 200:
                data = response.json()
                return ImmotopSubmitResponse(
                    success=True,
                    import_seqnr=data.get("import_seqnr"),
                    beleg_seqnr=data.get("beleg_seqnr"),
                    message="Beleg erfolgreich erstellt",
                )
            else:
                return ImmotopSubmitResponse(
                    success=False,
                    message=f"Fehler: {response.status_code} - {response.text}",
                )

    def _get_mock_konten(self) -> list[Konto]:
        """Mock-Konten basierend auf dem Schweizer Immobilien-Kontenplan"""
        mock_data = [
            # Aufwand - Liegenschaftsunterhalt
            {"s_seqnr": 1, "kontonr": "4000", "bez": "Unterhalt und Reparaturen", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 2, "kontonr": "4010", "bez": "Hauswartung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 3, "kontonr": "4020", "bez": "Gartenunterhalt", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 4, "kontonr": "4030", "bez": "Reinigung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 5, "kontonr": "4040", "bez": "Schneeräumung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 6, "kontonr": "4050", "bez": "Lift und Förderanlagen", "nebenbuchtypnr": 1, "mandant_seqnr": 1},

            # Aufwand - Betriebskosten
            {"s_seqnr": 10, "kontonr": "4100", "bez": "Heizung und Warmwasser", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 11, "kontonr": "4110", "bez": "Brennstoffe (Heizöl, Gas)", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 12, "kontonr": "4120", "bez": "Strom Allgemein", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 13, "kontonr": "4130", "bez": "Wasser und Abwasser", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 14, "kontonr": "4140", "bez": "Kehricht und Entsorgung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 15, "kontonr": "4150", "bez": "TV/Radio/Kabelgebühren", "nebenbuchtypnr": 1, "mandant_seqnr": 1},

            # Aufwand - Versicherungen
            {"s_seqnr": 20, "kontonr": "4200", "bez": "Gebäudeversicherung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 21, "kontonr": "4210", "bez": "Haftpflichtversicherung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 22, "kontonr": "4220", "bez": "Sachversicherung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},

            # Aufwand - Verwaltung
            {"s_seqnr": 30, "kontonr": "4300", "bez": "Verwaltungshonorar", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 31, "kontonr": "4310", "bez": "Buchhaltungskosten", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 32, "kontonr": "4320", "bez": "Rechtsberatung", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 33, "kontonr": "4330", "bez": "Bankspesen", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 34, "kontonr": "4340", "bez": "Porto und Telefon", "nebenbuchtypnr": 1, "mandant_seqnr": 1},

            # Aufwand - Steuern und Abgaben
            {"s_seqnr": 40, "kontonr": "4400", "bez": "Liegenschaftssteuer", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 41, "kontonr": "4410", "bez": "Grundstückgewinnsteuer", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 42, "kontonr": "4420", "bez": "Öffentliche Abgaben", "nebenbuchtypnr": 1, "mandant_seqnr": 1},

            # Aufwand - Spezifisch
            {"s_seqnr": 50, "kontonr": "4500", "bez": "Erneuerungsfonds", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 51, "kontonr": "4510", "bez": "Rückstellungen", "nebenbuchtypnr": 1, "mandant_seqnr": 1},
            {"s_seqnr": 52, "kontonr": "4520", "bez": "Abschreibungen", "nebenbuchtypnr": 1, "mandant_seqnr": 1},

            # Hauptbuch - Aktiven
            {"s_seqnr": 100, "kontonr": "1000", "bez": "Kasse", "nebenbuchtypnr": None, "mandant_seqnr": 1},
            {"s_seqnr": 101, "kontonr": "1020", "bez": "Bank", "nebenbuchtypnr": None, "mandant_seqnr": 1},
            {"s_seqnr": 102, "kontonr": "1100", "bez": "Debitoren", "nebenbuchtypnr": 2, "mandant_seqnr": 1},

            # Hauptbuch - Passiven
            {"s_seqnr": 110, "kontonr": "2000", "bez": "Kreditoren", "nebenbuchtypnr": None, "mandant_seqnr": 1},
            {"s_seqnr": 111, "kontonr": "2100", "bez": "MWST-Schuld", "nebenbuchtypnr": None, "mandant_seqnr": 1},
        ]
        return [Konto(**item) for item in mock_data]

    def _get_mock_kreditoren(self) -> list[Kreditor]:
        """Mock-Kreditoren für Tests"""
        mock_data = [
            {
                "s_seqnr": 1,
                "nr": 1001,
                "name": "Müller",
                "vorname": "Hans",
                "bez": "Müller Hauswartung GmbH",
                "strasse": "Bahnhofstrasse 10",
                "plz": "8001",
                "ort": "Zürich",
                "email": "info@mueller-hauswartung.ch",
                "frist1": 30,
            },
            {
                "s_seqnr": 2,
                "nr": 1002,
                "name": "Schweizer Heizöl AG",
                "vorname": None,
                "bez": "Schweizer Heizöl AG",
                "strasse": "Industriestrasse 5",
                "plz": "8304",
                "ort": "Wallisellen",
                "email": "bestellung@heizoel.ch",
                "mwstregisternr": "CHE-123.456.789 MWST",
                "frist1": 30,
            },
            {
                "s_seqnr": 3,
                "nr": 1003,
                "name": "Reinigung Express",
                "vorname": None,
                "bez": "Reinigung Express Sàrl",
                "strasse": "Route de Genève 20",
                "plz": "1003",
                "ort": "Lausanne",
                "email": "contact@reinigung-express.ch",
                "frist1": 14,
            },
            {
                "s_seqnr": 4,
                "nr": 1004,
                "name": "EWZ",
                "vorname": None,
                "bez": "Elektrizitätswerk der Stadt Zürich",
                "strasse": "Tramstrasse 35",
                "plz": "8050",
                "ort": "Zürich",
                "email": "info@ewz.ch",
                "frist1": 30,
            },
            {
                "s_seqnr": 5,
                "nr": 1005,
                "name": "Immo-Treuhand AG",
                "vorname": None,
                "bez": "Immo-Treuhand AG",
                "strasse": "Seestrasse 100",
                "plz": "8002",
                "ort": "Zürich",
                "email": "verwaltung@immo-treuhand.ch",
                "frist1": 30,
            },
            {
                "s_seqnr": 6,
                "nr": 1006,
                "name": "Schneider",
                "vorname": "Robert",
                "bez": "Robert Schneider AG",
                "strasse": "Rue du Lac 1268",
                "plz": "2501",
                "ort": "Biel",
                "email": "robert@rschneider.ch",
                "mwstregisternr": "CHE-123.456.789",
                "frist1": 30,
            },
            {
                "s_seqnr": 7,
                "nr": 1007,
                "name": "Grün & Co",
                "vorname": None,
                "bez": "Grün & Co Gartenbau",
                "strasse": "Gartenweg 15",
                "plz": "3000",
                "ort": "Bern",
                "email": "info@gruen-co.ch",
                "frist1": 30,
            },
            {
                "s_seqnr": 8,
                "nr": 1008,
                "name": "Wassermann AG",
                "vorname": None,
                "bez": "Wassermann AG",
                "strasse": "Wasserstrasse 1",
                "plz": "8001",
                "ort": "Zürich",
                "email": "info@wassermann.ch",
                "frist1": 30,
            },
        ]
        return [Kreditor(**item) for item in mock_data]

    def _mock_submit_beleg(
        self, mandant_seqnr: int, bruttobetrag: Decimal
    ) -> ImmotopSubmitResponse:
        """Mock-Response für Beleg-Erstellung"""
        import random

        return ImmotopSubmitResponse(
            success=True,
            import_seqnr=random.randint(10000, 99999),
            beleg_seqnr=random.randint(10000, 99999),
            message=f"[MOCK] Beleg über CHF {bruttobetrag} erfolgreich erstellt",
            immotop_url=f"https://demo.immotop2.ch/beleg/{random.randint(10000, 99999)}",
        )


# Singleton Instance
immotop_client = ImmotopClient()
