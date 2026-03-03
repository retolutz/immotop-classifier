# Immotop Invoice Classifier

Automatische Rechnungsklassifikation für die Schweizer Immobilienbuchhaltung mit Immotop2-Integration.

## Features

- **Rechnungs-Upload**: PDF, PNG, JPG, TIFF, BMP
- **OCR-Extraktion**: Tesseract für Texterkennung, Schweizer QR-Rechnung Support
- **KI-Klassifikation**: Claude (Anthropic) für semantische Kontozuordnung
- **Konfidenz-Score**: Zeigt Sicherheit der Zuordnung an
- **Immotop2-Integration**: Direkte Beleg-Erstellung via REST API

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  - Drag & Drop Upload                                       │
│  - Rechnungsvorschau                                        │
│  - Kontenzuordnung mit Konfidenz                            │
│  - Immotop2 Submit                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  - OCR Service (Tesseract/pdf2image)                        │
│  - LLM Classifier (Claude API)                              │
│  - Immotop2 REST Client                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Immotop2 API                              │
│  - SaveDmsImport (Beleg erstellen)                          │
│  - GetDmsKonto (Kontenplan)                                 │
│  - GetDmsKreditor (Kreditoren)                              │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Voraussetzungen

- Python 3.10+
- Node.js 18+
- Tesseract OCR (`brew install tesseract` auf macOS)
- Anthropic API Key

### Installation

```bash
# Repository klonen
cd immotop_nicolas

# Backend Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# .env erstellen und API Key eintragen
cp .env.example .env
# ANTHROPIC_API_KEY=sk-ant-api03-xxx eintragen

# Frontend Setup
cd ../frontend
npm install
cp .env.local.example .env.local
```

### Starten

```bash
# Option 1: Einzeln starten
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Option 2: Mit Start-Script
chmod +x start.sh
./start.sh
```

### Zugriff

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Konfiguration

### Backend (.env)

```env
# App
DEBUG=true

# Immotop2 API
IMMOTOP_API_URL=https://your-instance.immotop2.ch/api
IMMOTOP_USERNAME=wwdms
IMMOTOP_PASSWORD=your-password
IMMOTOP_MOCK_MODE=true  # Auf false setzen für echte API

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Mock-Modus

Im Mock-Modus werden Beispiel-Konten und Kreditoren verwendet. Zum Testen der echten Immotop2-Integration:

1. `IMMOTOP_MOCK_MODE=false` setzen
2. Echte Immotop2 Zugangsdaten eintragen

## API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/health` | GET | Health Check |
| `/api/konten` | GET | Kontenplan laden |
| `/api/kreditoren` | GET | Kreditoren laden |
| `/api/upload` | POST | Rechnung hochladen & klassifizieren |
| `/api/submit` | POST | Beleg an Immotop2 senden |

## Kontenplan

Der Klassifikator verwendet den Schweizer KMU-Kontenplan für Immobilienbuchhaltung:

- **4000-4050**: Unterhalt (Hauswart, Reinigung, Garten, Lift)
- **4100-4150**: Betriebskosten (Heizung, Strom, Wasser, Kehricht)
- **4200-4220**: Versicherungen
- **4300-4340**: Verwaltung
- **4400-4420**: Steuern und Abgaben
- **4500-4520**: Rückstellungen

## Technologie-Stack

### Backend
- FastAPI
- Anthropic Claude API
- Tesseract OCR
- pdf2image
- httpx

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- react-dropzone
- Lucide Icons

## Lizenz

Proprietär - W&W Immo Informatik AG
