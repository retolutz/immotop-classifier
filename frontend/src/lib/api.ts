/**
 * API Client für das Backend
 */

import type {
  InvoiceUploadResponse,
  ImmotopSubmitRequest,
  ImmotopSubmitResponse,
  Konto,
  Kreditor,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Health Check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request("/health");
  }

  /**
   * Lädt alle Konten
   */
  async getKonten(mandantSeqnr: number = 1): Promise<Konto[]> {
    return this.request(`/konten?mandant_seqnr=${mandantSeqnr}`);
  }

  /**
   * Lädt alle Kreditoren
   */
  async getKreditoren(mandantSeqnr: number = 1): Promise<Kreditor[]> {
    return this.request(`/kreditoren?mandant_seqnr=${mandantSeqnr}`);
  }

  /**
   * Lädt eine Rechnung hoch und klassifiziert sie
   */
  async uploadInvoice(file: File): Promise<InvoiceUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);

    return this.request("/upload", {
      method: "POST",
      body: formData,
    });
  }

  /**
   * Sendet eine Rechnung an Immotop2
   */
  async submitToImmotop(
    request: ImmotopSubmitRequest
  ): Promise<ImmotopSubmitResponse> {
    return this.request("/submit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });
  }

  /**
   * Löscht eine gecachte Rechnung
   */
  async deleteInvoice(invoiceId: string): Promise<void> {
    await this.request(`/invoice/${invoiceId}`, {
      method: "DELETE",
    });
  }
}

export const api = new ApiClient();
