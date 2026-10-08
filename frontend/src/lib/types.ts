export interface User {
  id: number;
  username: string;
  email: string;
  role: "admin" | "user" | string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface TrendPoint {
  date: string;
  avg_sentiment: number;
}

export interface KeywordItem {
  keyword: string;
  frequency: number;
}

export interface DashboardSummary {
  total_reviews: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_percent: number;
  negative_percent: number;
  neutral_percent: number;
  avg_sentiment: number;
  trend: TrendPoint[];
  top_keywords: KeywordItem[];
}

export type RiskLevel = "low" | "medium" | "high";

export interface AlertStatus {
  risk_level: RiskLevel;
  negative_percent: number;
  total_reviews: number;
  top_issues: string[];
  threshold: number;
}

export interface ReviewItem {
  review: string;
  sentiment: number;
  date: string;
}

export interface ReviewsResponse {
  reviews: ReviewItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface UploadSummary {
  total_processed: number;
  positive: number;
  negative: number;
  neutral: number;
  negative_percent: number;
  alert_triggered: boolean;
}

export type ClusteringMode = "negative" | "positive";

export interface ClusteringJobStatus {
  job_id: string;
  status: "pending" | "running" | "completed" | "failed";
  message?: string | null;
}

export interface ClusterItem {
  id: number;
  name: string;
  count: number;
  percentage: number;
  example_reviews: string[];
}

export interface ClusteringResult {
  success: boolean;
  message: string;
  total_reviews: number;
  n_clusters: number;
  noise_percentage: number;
  clusters: ClusterItem[];
}

export interface ChatRequest {
  question: string;
  session_id?: string;
  use_memory?: boolean;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
  session_id?: string | null;
  demo: boolean;
}

export interface AdminUser {
  id: number;
  username: string;
  role: string;
  created_at: string;
  review_count: number;
}
