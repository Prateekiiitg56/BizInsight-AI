const rawBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const API_BASE_URL = rawBaseUrl.replace(/\/+$/, "");

interface FetchOptions extends RequestInit {
  token?: string | null;
}

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { token, headers: customHeaders, ...restOptions } = options;
  const url = `${API_BASE_URL}${path}`;

  const headers = new Headers(customHeaders);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    headers,
    ...restOptions,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "An unexpected error occurred.");
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  async login(body: any) {
    return request<any>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async register(body: any) {
    return request<any>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async me(token: string) {
    return request<any>("/api/auth/me", {
      method: "GET",
      token,
    });
  },

  async googleLogin(body: { id_token: string }) {
    return request<any>("/api/auth/google", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  // Dashboard
  async getSummary(token: string) {
    return request<any>("/api/dashboard/summary", {
      method: "GET",
      token,
    });
  },

  async getAlerts(token: string) {
    return request<any>("/api/dashboard/alerts", {
      method: "GET",
      token,
    });
  },

  // Reviews
  async getReviews(token: string, page = 1, pageSize = 50) {
    return request<any>(`/api/reviews?page=${page}&page_size=${pageSize}`, {
      method: "GET",
      token,
    });
  },

  async uploadReviews(token: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);

    return request<any>("/api/reviews/upload", {
      method: "POST",
      body: formData,
      token,
    });
  },

  getExportUrl(token: string) {
    return `${API_BASE_URL}/api/reviews/export?token=${encodeURIComponent(token || "")}`;
  },

  // Clustering
  async startClustering(token: string, mode: "negative" | "positive" = "negative") {
    return request<any>("/api/clustering/run", {
      method: "POST",
      body: JSON.stringify({ mode }),
      token,
    });
  },

  async getClusteringStatus(token: string, jobId: string) {
    return request<any>(`/api/clustering/status/${jobId}`, {
      method: "GET",
      token,
    });
  },

  async getClusteringResults(token: string, jobId: string) {
    return request<any>(`/api/clustering/results/${jobId}`, {
      method: "GET",
      token,
    });
  },

  // RAG Chat
  async chat(token: string, body: { question: string; session_id?: string; use_memory?: boolean }) {
    return request<any>("/api/rag/chat", {
      method: "POST",
      body: JSON.stringify(body),
      token,
    });
  },

  // Admin
  async getUsers(token: string) {
    return request<any>("/api/admin/users", {
      method: "GET",
      token,
    });
  },

  async deleteUser(token: string, userId: number) {
    return request<any>(`/api/admin/users/${userId}`, {
      method: "DELETE",
      token,
    });
  },

  async clearReviews(token: string) {
    return request<any>("/api/admin/reviews", {
      method: "DELETE",
      token,
    });
  },
};
