from pydantic import BaseModel
from typing import Optional
from datetime import date


class Konto(BaseModel):
    """Konto aus dem Immotop2 Kontenplan"""

    s_seqnr: int
    kontonr: str
    bez: str
    nebenbuchtypnr: Optional[int] = None  # 1=Kostenbuch, 2=Debitorenbuch, 3=Kapitalbuch, NULL=Hauptbuch
    mandant_seqnr: int
    stufe: Optional[int] = None
    istkostenstellepflicht: bool = False
    istmengepflicht: bool = False
    einheit: Optional[str] = None
    mwstcode_seqnr: Optional[int] = None
    gueltigvon: Optional[date] = None
    gueltigbis: Optional[date] = None

    @property
    def nebenbuch_typ_name(self) -> str:
        mapping = {
            1: "Kostenbuch",
            2: "Debitorenbuch",
            3: "Kapitalbuch",
            None: "Hauptbuch",
        }
        return mapping.get(self.nebenbuchtypnr, "Unbekannt")


class Kreditor(BaseModel):
    """Kreditor aus Immotop2"""

    s_seqnr: int
    nr: Optional[int] = None
    name: str
    vorname: Optional[str] = None
    bez: str  # Bezeichnung
    strasse: Optional[str] = None
    plz: Optional[str] = None
    ort: Optional[str] = None
    email: Optional[str] = None
    mwstregisternr: Optional[str] = None
    frist1: int = 30  # Zahlungsfrist in Tagen

    @property
    def full_name(self) -> str:
        if self.vorname:
            return f"{self.vorname} {self.name}"
        return self.name

    @property
    def full_address(self) -> str:
        parts = []
        if self.strasse:
            parts.append(self.strasse)
        if self.plz and self.ort:
            parts.append(f"{self.plz} {self.ort}")
        elif self.ort:
            parts.append(self.ort)
        return ", ".join(parts)
