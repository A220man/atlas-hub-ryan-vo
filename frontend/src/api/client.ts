import {
  UserPrincipal,
  PresentationSummary,
  PresentationDetail,
  PaginatedResponse,
  EvaluationScorecard,
  NarrationPlan,
  TemplateTheme,
  AdvisoryResponse,
} from "../types/index.ts";

let inMemoryToken: string | null = null;

export const setAuthToken = (token: string | null) => {
  inMemoryToken = token;
};

export const getAuthToken = (): string | null => {
  return inMemoryToken;
};

async function apiFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");

  if (inMemoryToken) {
    headers.set("Authorization", `Bearer ${inMemoryToken}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore json parse error on raw error responses
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const apiClient = {
  async demoLogin(role = "analyst"): Promise<{ access_token: string; user: UserPrincipal }> {
    const data = await apiFetch<{ access_token: string; user: UserPrincipal }>("/api/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ role }),
    });
    setAuthToken(data.access_token);
    return data;
  },

  async fetchMe(): Promise<UserPrincipal> {
    return apiFetch<UserPrincipal>("/api/auth/me");
  },

  async logout(): Promise<void> {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } finally {
      setAuthToken(null);
    }
  },

  async listPresentations(params: {
    page?: number;
    size?: number;
    topic?: string;
    search?: string;
  } = {}): Promise<PaginatedResponse<PresentationSummary>> {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.size) query.set("size", String(params.size));
    if (params.topic) query.set("topic", params.topic);
    if (params.search) query.set("search", params.search);

    const qs = query.toString();
    return apiFetch<PaginatedResponse<PresentationSummary>>(`/api/presentations${qs ? `?${qs}` : ""}`);
  },

  async getPresentation(id: string): Promise<PresentationDetail> {
    return apiFetch<PresentationDetail>(`/api/presentations/${id}`);
  },

  async createPresentation(data: {
    title: string;
    topic?: string;
    raw_content: string;
    template_id?: string;
    aspect_ratio?: string;
  }): Promise<PresentationDetail> {
    return apiFetch<PresentationDetail>("/api/presentations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updatePresentation(
    id: string,
    data: { title?: string; template_id?: string; aspect_ratio?: string }
  ): Promise<PresentationSummary> {
    return apiFetch<PresentationSummary>(`/api/presentations/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  async deletePresentation(id: string): Promise<void> {
    await apiFetch<void>(`/api/presentations/${id}`, {
      method: "DELETE",
    });
  },

  async exportPptx(id: string): Promise<Blob> {
    const headers = new Headers();
    if (inMemoryToken) {
      headers.set("Authorization", `Bearer ${inMemoryToken}`);
    }
    const response = await fetch(`/api/presentations/${id}/export/pptx`, { headers });
    if (!response.ok) {
      throw new Error(`Failed to export PPTX: ${response.statusText}`);
    }
    return response.blob();
  },

  async runEvaluation(id: string): Promise<EvaluationScorecard> {
    return apiFetch<EvaluationScorecard>(`/api/presentations/${id}/evaluate`, {
      method: "POST",
    });
  },

  async getEvaluation(id: string): Promise<EvaluationScorecard> {
    return apiFetch<EvaluationScorecard>(`/api/presentations/${id}/evaluation`);
  },

  async generateNarration(
    id: string,
    data: { voice_id?: string; target_wpm?: number } = {}
  ): Promise<NarrationPlan> {
    return apiFetch<NarrationPlan>(`/api/presentations/${id}/narration`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async getNarration(id: string): Promise<NarrationPlan> {
    return apiFetch<NarrationPlan>(`/api/presentations/${id}/narration`);
  },

  async exportNarrationVtt(id: string): Promise<string> {
    const headers = new Headers();
    if (inMemoryToken) {
      headers.set("Authorization", `Bearer ${inMemoryToken}`);
    }
    const response = await fetch(`/api/presentations/${id}/narration/vtt`, { headers });
    if (!response.ok) {
      throw new Error(`Failed to export VTT: ${response.statusText}`);
    }
    return response.text();
  },

  async requestAdvisory(
    id: string,
    query_type = "executive_review",
    custom_instructions?: string
  ): Promise<AdvisoryResponse> {
    return apiFetch<AdvisoryResponse>(`/api/presentations/${id}/advisory`, {
      method: "POST",
      body: JSON.stringify({ query_type, custom_instructions }),
    });
  },

  async listTemplates(): Promise<TemplateTheme[]> {
    return apiFetch<TemplateTheme[]>("/api/templates");
  },
};
