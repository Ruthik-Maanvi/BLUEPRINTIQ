import type {
  AnalyzeResponse,
  AskResponse,
  HealthResponse,
  Material,
  MaterialWithReasoning,
  ProcurementPlan,
  ProjectOut,
  ProjectSummary,
  SearchResponse,
  UploadResponse,
} from "@/types/material";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://your-render-backend.onrender.com";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options?.body && !(options.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...options?.headers,
      },
    });
  } catch (error) {
    // This catches the exact "Failed to fetch" network crash
    throw new ApiError("Network error: Backend server is unreachable or crashed during processing.", 503);
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }
  
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  listProjects: () => request<ProjectSummary[]>("/projects"),

  getProject: (projectId: number) =>
    request<ProjectOut>(`/project/${projectId}`),

  uploadFiles: (files: File[], opts: { projectName?: string; projectId?: number }) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    if (opts.projectId !== undefined) {
      form.append("project_id", String(opts.projectId));
    } else if (opts.projectName) {
      form.append("project_name", opts.projectName);
    }
    return request<UploadResponse>("/upload", { method: "POST", body: form });
  },

  analyzeProject: (projectId: number) =>
    request<AnalyzeResponse>(`/analyze/${projectId}`, { method: "POST" }),

  getMaterials: (projectId: number) =>
    request<Material[]>(`/materials/${projectId}`),

  getProcurement: (projectId: number) =>
    request<ProcurementPlan>(`/procurement/${projectId}`),

  getReasoning: (projectId: number) =>
    request<MaterialWithReasoning[]>(`/reasoning/${projectId}`),

  search: (q: string, projectId?: number) => {
    const params = new URLSearchParams({ q });
    if (projectId !== undefined) params.set("project_id", String(projectId));
    return request<SearchResponse>(`/search?${params.toString()}`);
  },

  ask: (projectId: number, question: string) =>
    request<AskResponse>("/ask", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, question }),
    }),
};

export { ApiError };