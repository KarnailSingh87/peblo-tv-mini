import {
  AuthResponse,
  User,
  ShowListItem,
  ShowDetail,
  SeasonDetail,
  EpisodeDetail,
  ArtworkRecord,
  ValidationReport,
  PublishRun,
  PaginatedResponse
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

class ApiClient {
  private getToken(): string | null {
    return localStorage.getItem("peblo_cms_token");
  }

  public setToken(token: string | null): void {
    if (token) {
      localStorage.setItem("peblo_cms_token", token);
    } else {
      localStorage.removeItem("peblo_cms_token");
    }
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {})
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers
    });

    if (response.status === 401) {
      this.setToken(null);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login?expired=true";
      }
      throw new Error("Session expired. Please log in again.");
    }

    if (response.status === 204) {
      return null as unknown as T;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      let message = "An error occurred";
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (data.detail?.error) {
        message = data.detail.error;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((d: any) => `${d.loc?.join(".") || ""}: ${d.msg}`).join(", ");
      } else if (data.message) {
        message = data.message;
      }
      const error: any = new Error(message);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data as T;
  }

  // --- Auth APIs ---
  async login(credentials: { username: string; password: string }): Promise<AuthResponse> {
    const data = await this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials)
    });
    this.setToken(data.access_token);
    return data;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  // --- Shows APIs ---
  async listShows(params: {
    page?: number;
    page_size?: number;
    section?: string;
    status?: string;
    category?: string;
    search?: string;
  } = {}): Promise<PaginatedResponse<ShowListItem>> {
    const query = new URLSearchParams();
    if (params.page) query.set("page", params.page.toString());
    if (params.page_size) query.set("page_size", params.page_size.toString());
    if (params.section) query.set("section", params.section);
    if (params.status) query.set("status", params.status);
    if (params.category) query.set("category", params.category);
    if (params.search) query.set("search", params.search);

    return this.request<PaginatedResponse<ShowListItem>>(`/shows?${query.toString()}`);
  }

  async getShow(id: string): Promise<ShowDetail> {
    return this.request<ShowDetail>(`/shows/${id}`);
  }

  async createShow(payload: {
    title: string;
    slug: string;
    section?: string | null;
    categories?: string[];
    synopsis?: string | null;
    status?: "draft" | "published";
  }): Promise<ShowDetail> {
    return this.request<ShowDetail>("/shows", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  async updateShow(id: string, payload: Partial<ShowDetail>): Promise<ShowDetail> {
    return this.request<ShowDetail>(`/shows/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  }

  async deleteShow(id: string): Promise<void> {
    return this.request<void>(`/shows/${id}`, {
      method: "DELETE"
    });
  }

  // --- Seasons APIs ---
  async listShowSeasons(showId: string): Promise<SeasonDetail[]> {
    return this.request<SeasonDetail[]>(`/shows/${showId}/seasons`);
  }

  async createShowSeason(showId: string, payload: {
    season_number: number;
    title?: string;
  }): Promise<SeasonDetail> {
    return this.request<SeasonDetail>(`/shows/${showId}/seasons`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  // --- Episodes APIs ---
  async listSeasonEpisodes(seasonId: string): Promise<EpisodeDetail[]> {
    return this.request<EpisodeDetail[]>(`/seasons/${seasonId}/episodes`);
  }

  async createSeasonEpisode(seasonId: string, payload: {
    custom_id?: string;
    episode_number: number;
    episode_title: string;
    duration_seconds?: number | null;
    language: "en" | "hi";
    content_group: string;
    status: "draft" | "published";
    artwork_available?: string[];
  }): Promise<EpisodeDetail> {
    return this.request<EpisodeDetail>(`/seasons/${seasonId}/episodes`, {
      method: "POST",
      body: JSON.stringify(payload)
    });
  }

  async getEpisode(id: string): Promise<EpisodeDetail> {
    return this.request<EpisodeDetail>(`/episodes/${id}`);
  }

  async updateEpisode(id: string, payload: Partial<EpisodeDetail>): Promise<EpisodeDetail> {
    return this.request<EpisodeDetail>(`/episodes/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  }

  async deleteEpisode(id: string): Promise<void> {
    return this.request<void>(`/episodes/${id}`, {
      method: "DELETE"
    });
  }

  // --- Artwork APIs ---
  async uploadArtwork(formData: FormData): Promise<ArtworkRecord> {
    return this.request<ArtworkRecord>("/artwork/upload", {
      method: "POST",
      body: formData
    });
  }

  // --- Admin & Publishing APIs ---
  async getValidationReport(): Promise<ValidationReport> {
    return this.request<ValidationReport>("/admin/validation-report");
  }

  async publishCatalog(): Promise<any> {
    return this.request<any>("/admin/catalog/publish", {
      method: "POST"
    });
  }

  async getPublishRuns(): Promise<PublishRun[]> {
    return this.request<PublishRun[]>("/admin/catalog/publish-runs");
  }
}

export const api = new ApiClient();
