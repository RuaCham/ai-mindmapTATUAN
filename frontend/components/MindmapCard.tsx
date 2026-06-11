"use client";
// components/MindmapCard.tsx

import { useState } from "react";

interface MindmapMeta {
  id:              string;
  title:           string;
  source_pdf_name: string;
  num_nodes:       number;
  num_pages:       number;
  summary:         string;
  preview_url:     string | null;
  created_at:      string;
}

interface Props {
  mindmap:   MindmapMeta;
  onOpen:    (id: string) => void;
  onDelete:  (id: string) => void;
  onDownload:(id: string) => void;
}

export default function MindmapCard({ mindmap, onOpen, onDelete, onDownload }: Props) {
  const [deleting, setDeleting] = useState(false);

  const date = new Date(mindmap.created_at).toLocaleDateString("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });

  async function handleDelete() {
    if (!confirm("Xoá mindmap này?")) return;
    setDeleting(true);
    onDelete(mindmap.id);
  }

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden hover:border-gray-500 transition group">

      {/* Preview image */}
      <div className="h-36 bg-gray-900 flex items-center justify-center relative overflow-hidden">
        {mindmap.preview_url ? (
          <img
            src={`http://localhost:8000${mindmap.preview_url}`}
            alt={mindmap.title}
            className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition"
          />
        ) : (
          <span className="text-5xl opacity-20">🧠</span>
        )}
        {/* Overlay nút Open */}
        <button
          onClick={() => onOpen(mindmap.id)}
          className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/40 transition"
        >
          <span className="opacity-0 group-hover:opacity-100 transition bg-blue-600 text-white text-sm font-semibold px-4 py-2 rounded-lg">
            Mở Mindmap
          </span>
        </button>
      </div>

      {/* Info */}
      <div className="p-4">
        <h3 className="text-gray-100 font-semibold text-sm truncate mb-1">
          {mindmap.title}
        </h3>
        <p className="text-gray-500 text-xs truncate mb-2">
          📄 {mindmap.source_pdf_name}
        </p>

        {mindmap.summary && (
          <p className="text-gray-400 text-xs line-clamp-2 mb-3">
            {mindmap.summary}
          </p>
        )}

        <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
          <span>🔵 {mindmap.num_nodes} nodes</span>
          <span>📄 {mindmap.num_pages} trang</span>
        </div>

        <p className="text-gray-600 text-xs mb-3">{date}</p>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={() => onOpen(mindmap.id)}
            className="flex-1 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 text-xs py-1.5 rounded-lg transition"
          >
            Mở
          </button>
          <button
            onClick={() => onDownload(mindmap.id)}
            className="flex-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs py-1.5 rounded-lg transition"
          >
            JSON
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="bg-red-900/30 hover:bg-red-900/60 text-red-400 text-xs px-3 py-1.5 rounded-lg transition"
          >
            {deleting ? "..." : "🗑"}
          </button>
        </div>
      </div>
    </div>
  );
}
