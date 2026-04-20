export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "";

export type Paper = {
  paper_id: string;
  title: string;
  authors: string;
  abstract: string;
  doi: string;
  published_date: string;
  pdf_url: string;
  url: string;
  source: string;
  updated_date?: string;
  categories?: string;
  keywords?: string;
  citations?: number;
  references?: string;
  extra?: string;
};

export type SearchRequest = {
  query: string;
  sources: string[];
  max_results_per_source: number;
  year?: string | null;
};

export type SearchResponse = {
  query: string;
  sources_requested: string[];
  sources_used: string[];
  source_results: Record<string, number>;
  errors: Record<string, string>;
  papers: Paper[];
  total: number;
  raw_total: number;
};

export type SourceInfo = {
  key: string;
  label: string;
  note?: string | null;
};

export type SourcesResponse = {
  sources: SourceInfo[];
};

export type DownloadRequest = {
  source: string;
  paper_id: string;
  doi?: string;
  title?: string;
  use_scihub?: boolean;
};

export type DownloadResponse = {
  ok: boolean;
  message: string;
  path?: string | null;
};

async function request<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(headers ?? {}),
    },
    body: json !== undefined ? JSON.stringify(json) : init.body,
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = "";
    try {
      const data = (await res.json()) as { detail?: string };
      detail = data.detail ?? "";
    } catch {
      detail = await res.text();
    }
    throw new Error(
      detail || `Request to ${path} failed with status ${res.status}`,
    );
  }

  return (await res.json()) as T;
}

export function fetchSources(): Promise<SourcesResponse> {
  return request<SourcesResponse>("/api/sources", { method: "GET" });
}

export function searchPapers(req: SearchRequest): Promise<SearchResponse> {
  return request<SearchResponse>("/api/search", {
    method: "POST",
    json: req,
  });
}

export function downloadPaper(req: DownloadRequest): Promise<DownloadResponse> {
  return request<DownloadResponse>("/api/download", {
    method: "POST",
    json: req,
  });
}
