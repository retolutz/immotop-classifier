#!/usr/bin/env python3
"""
Qualitätstest für die Rechnungsklassifizierung
Testet 20 verschiedene Rechnungstypen gegen die erwarteten Konten
"""

import json
import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional

API_URL = "https://immotop-classifier.onrender.com/api"

@dataclass
class TestCase:
    """Ein Testfall für die Klassifikation"""
    name: str
    text: str
    expected_konto: str
    expected_konto_name: str
    category: str


# 20 Testfälle für verschiedene Schweizer Rechnungstypen
TEST_CASES = [
    # 1. Gartenunterhalt
    TestCase(
        name="Gartenarbeiten Schneider",
        text="""
        Robert Schneider AG
        Rue du Lac 1268, 2501 Biel

        Rechnung Nr. 10201409
        Datum: 01.07.2024

        Gartenarbeiten                    12.5 Std.    CHF 120.00    CHF 1'500.00
        Entsorgung Schnittmaterial        1            CHF 310.35    CHF 310.35

        Rechnungstotal CHF 1'949.75 inkl. MwSt.
        """,
        expected_konto="4020",
        expected_konto_name="Gartenunterhalt",
        category="Unterhalt"
    ),

    # 2. Heizöl
    TestCase(
        name="Heizöl-Lieferung",
        text="""
        Schweizer Heizöl AG
        Industriestrasse 5, 8304 Wallisellen

        Rechnung Nr. 2024-1234

        Heizöl extra leicht              3000 Liter   CHF 0.95/L
        Lieferung und Pumpen             pauschal     CHF 85.00

        Zwischensumme                                  CHF 2'935.00
        MwSt. 8.1%                                     CHF 237.74
        Rechnungstotal                                 CHF 3'172.74

        IBAN: CH44 3199 9123 0008 8901 2
        """,
        expected_konto="4110",
        expected_konto_name="Brennstoffe (Heizöl, Gas)",
        category="Betriebskosten"
    ),

    # 3. Strom
    TestCase(
        name="Stromrechnung EWZ",
        text="""
        Elektrizitätswerk der Stadt Zürich (EWZ)
        Tramstrasse 35, 8050 Zürich

        Stromrechnung Januar - März 2024
        Zählernummer: 123456789

        Verbrauch Allgemeinstrom          1'250 kWh
        Grundgebühr                       CHF 45.00
        Energiekosten                     CHF 312.50
        Netznutzung                       CHF 87.50
        Abgaben KEV/StromVG               CHF 25.00

        Total inkl. MwSt.                 CHF 470.00
        """,
        expected_konto="4120",
        expected_konto_name="Strom Allgemein",
        category="Betriebskosten"
    ),

    # 4. Wasser/Abwasser
    TestCase(
        name="Wasserrechnung",
        text="""
        Wasserversorgung Stadt Bern
        Wassergasse 10, 3000 Bern

        Jahresrechnung Wasser und Abwasser 2024
        Liegenschaft: Musterstrasse 123

        Wasserverbrauch                   150 m³       CHF 225.00
        Abwassergebühr                    150 m³       CHF 180.00
        Grundgebühr Wasser                             CHF 120.00
        Grundgebühr Abwasser                           CHF 85.00

        Gesamtbetrag                                   CHF 610.00
        """,
        expected_konto="4130",
        expected_konto_name="Wasser und Abwasser",
        category="Betriebskosten"
    ),

    # 5. Hauswartung
    TestCase(
        name="Hauswart-Rechnung",
        text="""
        Müller Hauswartung GmbH
        Bahnhofstrasse 10, 8001 Zürich

        Rechnung für Hauswartungsarbeiten
        Objekt: Seestrasse 45, Zürich
        Monat: März 2024

        Hauswartlohn (40 Std. à CHF 45.-)              CHF 1'800.00
        Sozialabgaben (ca. 15%)                        CHF 270.00
        Reinigungsmaterial                             CHF 125.00
        Kleinreparaturen Material                      CHF 85.00

        Total exkl. MwSt.                              CHF 2'280.00
        MwSt. 8.1%                                     CHF 184.68
        Rechnungstotal                                 CHF 2'464.68
        """,
        expected_konto="4010",
        expected_konto_name="Hauswartung",
        category="Unterhalt"
    ),

    # 6. Reinigung
    TestCase(
        name="Treppenhausreinigung",
        text="""
        Reinigung Express Sàrl
        Route de Genève 20, 1003 Lausanne

        Facture / Rechnung

        Nettoyage cage d'escalier / Treppenhausreinigung
        Immeuble / Gebäude: Avenue de la Gare 15
        Période / Zeitraum: 01.03. - 31.03.2024

        Reinigung Treppenhaus wöchentlich   4x         CHF 320.00
        Fensterreinigung Eingang            1x         CHF 85.00
        Reinigungsmittel                               CHF 45.00

        Montant total / Gesamtbetrag                   CHF 450.00
        """,
        expected_konto="4030",
        expected_konto_name="Reinigung",
        category="Unterhalt"
    ),

    # 7. Lift/Aufzug
    TestCase(
        name="Lift-Wartung",
        text="""
        Schindler Aufzüge AG
        Zugerstrasse 13, 6030 Ebikon

        Rechnung Servicepauschale

        Wartungsvertrag Aufzugsanlage
        Objekt: Bahnhofstrasse 100, Zürich
        Anlage-Nr.: 12345678

        Service-Pauschale Q1/2024                      CHF 1'250.00
        Notdienst-Bereitschaft                         CHF 180.00

        Nettobetrag                                    CHF 1'430.00
        MwSt. 8.1%                                     CHF 115.83
        Total                                          CHF 1'545.83
        """,
        expected_konto="4050",
        expected_konto_name="Lift und Förderanlagen",
        category="Unterhalt"
    ),

    # 8. Gebäudeversicherung
    TestCase(
        name="Gebäudeversicherung Prämie",
        text="""
        Aargauische Gebäudeversicherung
        Bleichemattstrasse 12/14, 5000 Aarau

        Prämienrechnung 2024

        Versicherungsnehmer: Muster Immobilien AG
        Gebäude: Hauptstrasse 50, 5000 Aarau

        Feuerversicherung                              CHF 1'850.00
        Elementarschadenversicherung                   CHF 420.00
        Gebäudewasserversicherung                      CHF 380.00

        Jahresprämie Total                             CHF 2'650.00

        Zahlbar bis: 31.01.2024
        """,
        expected_konto="4200",
        expected_konto_name="Gebäudeversicherung",
        category="Versicherungen"
    ),

    # 9. Haftpflichtversicherung
    TestCase(
        name="Haftpflicht Liegenschaft",
        text="""
        Die Mobiliar
        Bundesgasse 35, 3001 Bern

        Police Nr.: 12.345.678
        Prämienrechnung

        Gebäudehaftpflichtversicherung
        Objekt: Seeweg 12, 6004 Luzern

        Jahresprämie Haftpflicht Liegenschaft          CHF 450.00
        inkl. Stempelabgabe

        Zahlbar innert 30 Tagen
        """,
        expected_konto="4210",
        expected_konto_name="Haftpflichtversicherung",
        category="Versicherungen"
    ),

    # 10. Verwaltungshonorar
    TestCase(
        name="Verwaltungshonorar",
        text="""
        Immo-Treuhand AG
        Seestrasse 100, 8002 Zürich

        Honorarrechnung Liegenschaftsverwaltung

        Verwaltungsobjekt: Bergstrasse 25, Zürich
        Periode: 01.01.2024 - 31.03.2024

        Verwaltungshonorar Q1/2024                     CHF 2'500.00
        Buchhaltung und Abrechnung                     CHF 450.00
        Porto und Telefon                              CHF 85.00

        Zwischensumme                                  CHF 3'035.00
        MwSt. 8.1%                                     CHF 245.84
        Rechnungstotal                                 CHF 3'280.84
        """,
        expected_konto="4300",
        expected_konto_name="Verwaltungshonorar",
        category="Verwaltung"
    ),

    # 11. Schneeräumung
    TestCase(
        name="Schneeräumung Winter",
        text="""
        Winterdienst Alpen GmbH
        Bergweg 5, 7270 Davos

        Rechnung Winterdienst

        Objekt: Promenade 10-14, Davos
        Zeitraum: Dezember 2023 - Februar 2024

        Schneeräumung Zufahrt             12 Einsätze  CHF 1'440.00
        Schneeräumung Gehweg              12 Einsätze  CHF 960.00
        Streusalz und Material                         CHF 280.00

        Total inkl. MwSt.                              CHF 2'680.00
        """,
        expected_konto="4040",
        expected_konto_name="Schneeräumung",
        category="Unterhalt"
    ),

    # 12. Kehricht/Entsorgung
    TestCase(
        name="Kehrichtgebühren",
        text="""
        Entsorgung + Recycling Zürich ERZ
        Hagenholzstrasse 110, 8050 Zürich

        Gebührenrechnung 2024

        Grundgebühr Kehrichtabfuhr                     CHF 320.00
        Grüngutcontainer 240L                          CHF 180.00
        Papiersammlung                                 CHF 60.00
        Sperrgutmarken (10 Stk.)                       CHF 150.00

        Gesamtbetrag                                   CHF 710.00
        """,
        expected_konto="4140",
        expected_konto_name="Kehricht und Entsorgung",
        category="Betriebskosten"
    ),

    # 13. TV/Kabel
    TestCase(
        name="Kabelanschluss",
        text="""
        UPC Schweiz GmbH
        Hardturmstrasse 3, 8005 Zürich

        Rechnung Kabelnetz

        Sammelanschluss Liegenschaft
        Adresse: Bahnhofweg 20, Zürich

        Grundgebühr TV-Anschluss (24 Einheiten)        CHF 2'160.00
        HD-Option                                      CHF 480.00

        Jahresbetrag                                   CHF 2'640.00
        MwSt. inkl.
        """,
        expected_konto="4150",
        expected_konto_name="TV/Radio/Kabelgebühren",
        category="Betriebskosten"
    ),

    # 14. Allgemeine Reparatur
    TestCase(
        name="Sanitär-Reparatur",
        text="""
        Sanitär Meier AG
        Werkstrasse 8, 8400 Winterthur

        Reparaturrechnung

        Objekt: Wohnung 3.OG links, Musterstr. 15

        Reparatur undichter Wasserhahn Küche
        Arbeitszeit                        2 Std.      CHF 180.00
        Material (Dichtungen, Kartusche)               CHF 65.00
        Anfahrt                                        CHF 45.00

        Total exkl. MwSt.                              CHF 290.00
        MwSt. 8.1%                                     CHF 23.49
        Rechnungstotal                                 CHF 313.49
        """,
        expected_konto="4000",
        expected_konto_name="Unterhalt und Reparaturen",
        category="Unterhalt"
    ),

    # 15. Rechtsberatung
    TestCase(
        name="Anwaltshonorar Mietrecht",
        text="""
        Kanzlei Recht & Partner
        Paradeplatz 5, 8001 Zürich

        Honorarnote

        Betreff: Beratung Mietvertragskündigung
        Mandant: Immo AG

        Rechtsberatung Mietrecht           3 Std.      CHF 900.00
        Korrespondenz und Telefonate       1 Std.      CHF 280.00
        Auslagen (Kopien, Porto)                       CHF 35.00

        Honorar netto                                  CHF 1'215.00
        MwSt. 8.1%                                     CHF 98.42
        Total                                          CHF 1'313.42
        """,
        expected_konto="4320",
        expected_konto_name="Rechtsberatung",
        category="Verwaltung"
    ),

    # 16. Buchhaltung extern
    TestCase(
        name="Buchhaltungskosten",
        text="""
        Treuhand Müller & Co.
        Bahnhofstrasse 50, 8001 Zürich

        Rechnung Buchhaltungsarbeiten

        Mandant: Immobilien XY AG
        Periode: Jahresabschluss 2023

        Erstellung Jahresrechnung                      CHF 2'800.00
        Nebenkostenabrechnung (8 Einheiten)            CHF 640.00
        Steuererklärung Liegenschaft                   CHF 450.00

        Total exkl. MwSt.                              CHF 3'890.00
        MwSt. 8.1%                                     CHF 315.09
        Rechnungstotal                                 CHF 4'205.09
        """,
        expected_konto="4310",
        expected_konto_name="Buchhaltungskosten",
        category="Verwaltung"
    ),

    # 17. Bankspesen
    TestCase(
        name="Bankgebühren Konto",
        text="""
        Credit Suisse
        Paradeplatz 8, 8001 Zürich

        Kontoauszug / Gebührenabrechnung

        Konto: Mietkautionen Nr. 123-456789-0

        Kontoführungsgebühr Q1/2024                    CHF 75.00
        Zahlungsverkehr (45 Buchungen)                 CHF 67.50
        E-Banking Pauschale                            CHF 15.00

        Belastung total                                CHF 157.50
        """,
        expected_konto="4330",
        expected_konto_name="Bankspesen",
        category="Verwaltung"
    ),

    # 18. Liegenschaftssteuer
    TestCase(
        name="Liegenschaftssteuer",
        text="""
        Gemeinde Küsnacht
        Steueramt
        Obere Dorfstrasse 32, 8700 Küsnacht

        Veranlagung Liegenschaftssteuer 2024

        Steuerpflichtiger: Immo Verwaltungs AG
        Grundstück: Seestrasse 150, 8700 Küsnacht

        Steuerwert Liegenschaft: CHF 2'450'000
        Steuersatz: 0.5‰

        Liegenschaftssteuer 2024                       CHF 1'225.00

        Zahlbar bis: 30.04.2024
        """,
        expected_konto="4400",
        expected_konto_name="Liegenschaftssteuer",
        category="Steuern"
    ),

    # 19. Gas-Rechnung
    TestCase(
        name="Erdgas-Lieferung",
        text="""
        Energie 360° AG
        Aargauerstrasse 182, 8010 Zürich

        Gasrechnung

        Verbrauchsstelle: Industrieweg 5, Zürich
        Abrechnungsperiode: 01.10.2023 - 31.12.2023

        Gasverbrauch                    5'200 kWh
        Arbeitspreis                                   CHF 520.00
        Grundpreis                                     CHF 85.00
        Netznutzung                                    CHF 156.00
        CO2-Abgabe                                     CHF 78.00

        Total inkl. MwSt.                              CHF 839.00
        """,
        expected_konto="4110",
        expected_konto_name="Brennstoffe (Heizöl, Gas)",
        category="Betriebskosten"
    ),

    # 20. Heizungswartung
    TestCase(
        name="Heizungswartung Service",
        text="""
        Hoval Herzog AG
        General Wille-Strasse 201, 8706 Feldmeilen

        Service-Rechnung

        Heizungsanlage: Ölbrenner Hoval TopGas
        Standort: Bergstrasse 45, 8700 Küsnacht

        Jährliche Wartung Heizkessel                   CHF 380.00
        Brenner-Service inkl. Düsenwechsel             CHF 220.00
        Rauchgasmessung und Protokoll                  CHF 85.00
        Anfahrtspauschale                              CHF 65.00

        Total exkl. MwSt.                              CHF 750.00
        MwSt. 8.1%                                     CHF 60.75
        Rechnungstotal                                 CHF 810.75
        """,
        expected_konto="4100",
        expected_konto_name="Heizung und Warmwasser",
        category="Betriebskosten"
    ),
]


async def test_classification(test_case: TestCase) -> dict:
    """Testet einen einzelnen Fall über die API"""
    # Wir simulieren einen Upload mit dem Text
    # Da wir kein echtes PDF haben, testen wir die LLM-Klassifikation direkt

    # Für diesen Test nutzen wir einen direkten API-Call
    # In Produktion würde man ein PDF hochladen

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Hole zuerst die Konten
        konten_response = await client.get(f"{API_URL}/konten")
        konten = konten_response.json()

        # Erstelle einen Mock-Request für die Klassifikation
        # Da es keinen direkten Klassifikations-Endpoint gibt,
        # loggen wir die erwarteten Ergebnisse

        return {
            "name": test_case.name,
            "expected_konto": test_case.expected_konto,
            "expected_name": test_case.expected_konto_name,
            "category": test_case.category,
            "text_preview": test_case.text[:100].strip(),
            "konten_available": len(konten),
        }


async def run_all_tests():
    """Führt alle Tests durch und gibt einen Bericht aus"""
    print("=" * 70)
    print("QUALITÄTSTEST: Rechnungsklassifizierung")
    print("=" * 70)
    print(f"\nAnzahl Testfälle: {len(TEST_CASES)}")
    print(f"API: {API_URL}")
    print("-" * 70)

    # Gruppiere nach Kategorie
    categories = {}
    for tc in TEST_CASES:
        if tc.category not in categories:
            categories[tc.category] = []
        categories[tc.category].append(tc)

    print("\nTestfälle nach Kategorie:")
    for cat, cases in categories.items():
        print(f"  {cat}: {len(cases)} Tests")
        for case in cases:
            print(f"    - {case.name} → erwarte Konto {case.expected_konto} ({case.expected_konto_name})")

    print("\n" + "=" * 70)
    print("Hinweis: Für echte API-Tests müssen die Texte als PDF hochgeladen werden.")
    print("Diese Testfälle dienen als Referenz für manuelle oder automatisierte Tests.")
    print("=" * 70)

    # Speichere Testfälle als JSON für spätere Verwendung
    test_data = [
        {
            "name": tc.name,
            "text": tc.text.strip(),
            "expected_konto": tc.expected_konto,
            "expected_name": tc.expected_konto_name,
            "category": tc.category,
        }
        for tc in TEST_CASES
    ]

    with open("test_cases.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    print(f"\nTestfälle gespeichert in: test_cases.json")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
