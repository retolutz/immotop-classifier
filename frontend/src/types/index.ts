// API Types - müssen mit Backend übereinstimmen

export interface AccountSuggestion {
  konto_seqnr: number;
  konto_nr: string;
  konto_bez: string;
  konfidenz: number;
  begruendung: string;
}

export interface ClassificationResult {
  primary: AccountSuggestion;
  alternativen: AccountSuggestion[];
  extrahierte_daten: Record<string, string | null>;
}

export interface InvoiceData {
  raw_text: string;
  kreditor_name: string | null;
  kreditor_adresse: string | null;
  rechnungsnummer: string | null;
  rechnungsdatum: string | null;
  faelligkeitsdatum: string | null;
  bruttobetrag: number | null;
  nettobetrag: number | null;
  mwst_betrag: number | null;
  mwst_satz: number | null;
  waehrung: string;
  iban: string | null;
  qr_referenz: string | null;
  beschreibung: string | null;
}

export interface InvoiceUploadResponse {
  id: string;
  filename: string;
  invoice_data: InvoiceData;
  classification: ClassificationResult;
  preview_url: string | null;
}

export interface Konto {
  s_seqnr: number;
  kontonr: string;
  bez: string;
  nebenbuchtypnr: number | null;
  mandant_seqnr: number;
}

export interface Kreditor {
  s_seqnr: number;
  nr: number | null;
  name: string;
  vorname: string | null;
  bez: string;
  strasse: string | null;
  plz: string | null;
  ort: string | null;
  email: string | null;
}

export interface BelegPosten {
  konto_seqnr: number;
  kostenstelle_seqnr: number | null;
  bruttobetrag: number;
  betrag_exkl_mwst: number | null;
  betrag_mwst: number | null;
  mwst_satz: number | null;
  mwst_code_seqnr: number | null;
  buchungstext: string;
}

export interface ImmotopSubmitRequest {
  invoice_id: string;
  mandant_seqnr: number;
  kreditor_seqnr: number | null;
  belegdatum: string;
  faelligkeitsdatum: string | null;
  bruttobetrag: number;
  buchungstext: string;
  positionen: BelegPosten[];
  // Zusätzliche Felder
  rechnungsnummer: string | null;
  esrreferenznummer: string | null;
  qrcodepayload: string | null;
  kreditor_iban: string | null;
}

export interface ImmotopSubmitResponse {
  success: boolean;
  import_seqnr: number | null;
  beleg_seqnr: number | null;
  message: string;
  immotop_url: string | null;
}
