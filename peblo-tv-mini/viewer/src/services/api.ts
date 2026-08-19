import { PublishedCatalogue, SearchResponse } from "../types";

/**
 * Peblo TV Viewer API Client
 *
 * ARCHITECTURAL CONSTRAINT:
 * The viewer application reads strictly from the compiled, immutable published catalogue.
 * It NEVER hits transactional CMS/admin endpoints, guaranteeing zero write contention,
 * instant sub-millisecond edge reading, and consistent catalogue snapshots.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const viewerApi = {
  /**
   * Fetch the full live published streaming catalogue
   */
  async getCatalog(): Promise<PublishedCatalogue> {
    const res = await fetch(`${API_BASE_URL}/catalog`);
    if (res.status === 404) {
      const error: any = new Error("No catalogue has been published yet.");
      error.status = 404;
      throw error;
    }
    if (!res.ok) {
      throw new Error(`Failed to load catalogue (HTTP ${res.status})`);
    }
    return res.json();
  },

  /**
   * Execute server-side search and filtering against the published catalogue
   */
  async searchCatalog(params: {
    q?: string;
    category?: string;
    language?: string;
    section?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q.trim());
    if (params.category) query.set("category", params.category);
    if (params.language) query.set("language", params.language);
    if (params.section) query.set("section", params.section);
    if (params.page) query.set("page", params.page.toString());
    if (params.page_size) query.set("page_size", params.page_size.toString());

    const res = await fetch(`${API_BASE_URL}/catalog/search?${query.toString()}`);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Search failed (HTTP ${res.status})`);
    }
    return res.json();
  }
};
