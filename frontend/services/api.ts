// services/api.ts
// Tất cả calls tới FastAPI backend

import { UploadResponse, MindmapResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// ── Upload PDF ─────────────────────────────────────────────────────────────────
export async function uploadPDF(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body:   formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Upload thất bại");
  }

  return res.json();
}

// ── Lấy Mindmap JSON ───────────────────────────────────────────────────────────
export async function getMindmap(
  fileId:       string,
  maxKeywords:  number = 15,
  topSentences: number = 5,
  numTopics:    number = 4,
): Promise<MindmapResponse> {
  const params = new URLSearchParams({
    max_keywords:  String(maxKeywords),
    top_sentences: String(topSentences),
    num_topics:    String(numTopics),
  });

  const res = await fetch(`${API_BASE}/mindmap/${fileId}?${params}`);

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Lỗi tạo mindmap");
  }

  return res.json();
}

// ── Lấy keywords nhanh ────────────────────────────────────────────────────────
export async function getKeywords(fileId: string, topN: number = 20) {
  const res = await fetch(`${API_BASE}/mindmap/${fileId}/keywords?top_n=${topN}`);
  if (!res.ok) throw new Error("Lỗi lấy keywords");
  return res.json();
}


// ── Mindmap Store API ──────────────────────────────────────────────────────────

export async function listSavedMindmaps(skip = 0, limit = 20) {
  const res = await fetch(`${API_BASE}/mindmaps?skip=${skip}&limit=${limit}`);
  if (!res.ok) throw new Error("Lỗi lấy danh sách");
  return res.json();
}

export async function getSavedMindmap(id: string) {
  const res = await fetch(`${API_BASE}/mindmaps/${id}`);
  if (!res.ok) throw new Error("Không tìm thấy mindmap");
  return res.json();
}

export async function saveMindmap(payload: {
  title:           string;
  source_pdf_name: string;
  source_pdf_path?: string;
  mindmap_data:    any;
  keywords:        Record<string, number>;
  num_pages:       number;
}) {
  const res = await fetch(`${API_BASE}/mindmaps/save`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Lỗi lưu mindmap");
  return res.json();
}

export async function deleteSavedMindmap(id: string) {
  const res = await fetch(`${API_BASE}/mindmaps/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Lỗi xoá");
  return res.json();
}

export async function downloadMindmapJSON(id: string, title: string) {
  const res  = await fetch(`${API_BASE}/mindmaps/${id}/download`);
  const blob = await res.blob();
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = `${title}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
