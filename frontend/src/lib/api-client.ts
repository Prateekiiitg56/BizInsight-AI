import { clearSession, getToken, UNAUTHORIZED_EVENT } from "./session";
import type {
  AdminUser,
  AlertStatus,
  AuthResponse,
  ChatRequest,
  ChatResponse,
  ClusteringJobStatus,
  ClusteringMode,
  ClusteringResult,
  DashboardSummary,
  ReviewsResponse,
  UploadSummary,
  User,
} from "./types";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "https://bizinsight-backend.onrender.com"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

const NETWORK_ERROR =
  "Can't reach the BizInsight server. If it was idle it may be starting up — please try again in a few seconds.";

function errorMessage(data: unknown, fallback: string): string {
  const detail = (data as { detail?: unknown })?.detail;
  if (typeof detail === "string") return detail;
  // FastAPI validation errors: [{ msg: "..." }]
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return detail[0].msg;
  return fallback;
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: BodyInit | object;
  auth?: boolean;
}

async function rawRequest(path: string, { body, auth = true, headers: extra, ...init }: RequestOptions = {}) {
  const headers = new Headers(extra);
  const token = auth ? getToken() : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let payload: BodyInit | undefined;
  if (body instanceof FormData || typeof body === "string" || body === undefined) {
    payload = body as BodyInit | undefined;
  } else {
    headers.set("Content-Type", "application/json");
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, body: payload });
  } catch {
    throw new ApiError(NETWORK_ERROR, 0);
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    if (response.status === 401 && token) {
      clearSession();
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    throw new ApiError(errorMessage(data, `Request failed (${response.status}).`), response.status);
  }
  return response;
}

async function request<T>(path: string, options?: RequestOptions): Promise<T> {
  const response = await rawRequest(path, options);
  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  login: (body: { username: string; password: string }) =>
    request<AuthResponse>("/api/auth/login", { method: "POST", body, auth: false }),

  register: (body: { username: string; email: string; password: string; confirm_password: string }) =>
    request<AuthResponse>("/api/auth/register", { method: "POST", body, auth: false }),

  me: () => request<User>("/api/auth/me"),

  async googleLogin(idToken: string): Promise<AuthResponse> {
    // Same-origin Next.js route that forwards to the backend server-to-server.
    let response: Response;
    try {
      response = await fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken }),
      });
    } catch {
      throw new ApiError(NETWORK_ERROR, 0);
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new ApiError(errorMessage(data, "Google sign-in failed."), response.status);
    return data as AuthResponse;
  },

  // Dashboard
  getSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  getAlerts: () => request<AlertStatus>("/api/dashboard/alerts"),

  // Reviews
  getReviews: (page = 1, pageSize = 50) =>
    request<ReviewsResponse>(`/api/reviews?page=${page}&page_size=${pageSize}`),

  uploadReviews(file: File) {
    const body = new FormData();
    body.append("file", file);
    return request<UploadSummary>("/api/reviews/upload", { method: "POST", body });
  },

  async exportReviews(): Promise<Blob> {
    const response = await rawRequest("/api/reviews/export");
    return response.blob();
  },

  clearReviews: () => request<{ status: string; message: string }>("/api/admin/reviews", { method: "DELETE" }),

  // Clustering
  startClustering: (mode: ClusteringMode) =>
    request<ClusteringJobStatus>("/api/clustering/run", { method: "POST", body: { mode } }),
  getClusteringStatus: (jobId: string) => request<ClusteringJobStatus>(`/api/clustering/status/${jobId}`),
  getClusteringResults: (jobId: string) => request<ClusteringResult>(`/api/clustering/results/${jobId}`),

  // RAG chat — sends the token when signed in; signed-out visitors get the demo dataset.
  chat: (body: ChatRequest) => request<ChatResponse>("/api/rag/chat", { method: "POST", body }),

  // Admin
  getUsers: () => request<{ users: AdminUser[] }>("/api/admin/users"),
  deleteUser: (userId: number) =>
    request<{ status: string; message: string }>(`/api/admin/users/${userId}`, { method: "DELETE" }),
};
