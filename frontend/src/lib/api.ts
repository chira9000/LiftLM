const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("liftai_token");
}

export function setToken(token: string) {
  localStorage.setItem("liftai_token", token);
}

export function clearToken() {
  localStorage.removeItem("liftai_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export interface User {
  id: number;
  email: string;
  name: string;
}

export interface DashboardStats {
  total_workouts: number;
  total_volume: number;
  total_sets: number;
  active_exercises: number;
  workouts_this_week: number;
  volume_this_week: number;
  recent_prs: { exercise: string; weight: number; reps: number; e1rm: number; date: string }[];
  volume_trend: { date: string; volume: number; workout_count: number }[];
  top_exercises: { name: string; volume: number }[];
}

export interface WorkoutSummary {
  id: number;
  name: string;
  performed_at: string;
  total_sets: number;
  total_volume: number;
  exercise_count: number;
}

export interface ExerciseAnalytics {
  exercise_id: number;
  exercise_name: string;
  muscle_group: string;
  total_sessions: number;
  total_sets: number;
  total_volume: number;
  estimated_1rm: number;
  estimated_1rm_trend: { date: string; estimated_1rm: number; top_set_weight: number; top_set_reps: number; volume: number }[];
  pr_weight: number;
  pr_reps: number;
  pr_date: string | null;
  avg_rpe: number | null;
  frequency_per_week: number;
  last_performed: string | null;
}

export interface ProgressionRecommendation {
  exercise_id: number;
  exercise_name: string;
  recommended_weight: number;
  recommended_reps: number;
  recommended_sets: number;
  progression_score: number;
  score_breakdown: Record<string, number>;
  rationale: string;
  last_session_summary: Record<string, unknown> | null;
}

export interface Exercise {
  id: number;
  name: string;
  muscle_group: string;
  equipment: string;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/auth/me"),

  dashboard: () => request<DashboardStats>("/analytics/dashboard"),

  workouts: () => request<WorkoutSummary[]>("/workouts"),

  workout: (id: number) => request<unknown>(`/workouts/${id}`),

  createWorkout: (data: unknown) =>
    request<unknown>("/workouts", { method: "POST", body: JSON.stringify(data) }),

  exercises: () => request<Exercise[]>("/exercises"),

  exerciseAnalytics: () => request<ExerciseAnalytics[]>("/analytics/exercises"),

  progression: () => request<ProgressionRecommendation[]>("/progression"),

  chat: (message: string, history: { role: string; content: string }[]) =>
    request<{ reply: string }>("/coach/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),
};
