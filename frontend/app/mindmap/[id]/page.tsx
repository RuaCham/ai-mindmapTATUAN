"use client";
// app/mindmap/[id]/page.tsx

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import MindMap from "@/components/MindMap";
import { downloadMindmapJSON } from "@/services/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export default function MindmapDetailPage({ params }: { params: { id: string } }) {
  const id     = params.id;
  const router = useRouter();

  const [data,    setData]    = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_BASE}/mindmaps/${id}`)
      .then(res => { if (!res.ok) throw new Error(`HTTP ${res.status}`); return res.json(); })
      .then(result => setData(result))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  const mindmapData = data?.mindmap_data;
  const nodes       = mindmapData?.nodes || [];
  const edges       = mindmapData?.edges || [];
  const stats       = mindmapData?.stats  || { total_nodes: 0, total_edges: 0, depth: 0, keywords: [] };
  const title       = data?.title || "Mindmap";

  return (
    // KEY FIX: dùng h-screen trực tiếp thay vì min-h-screen + flex flex-col
    <div style={{ width: "100vw", height: "100vh", display: "flex", flexDirection: "column", background: "#111827" }}>

      {/* Navbar — fixed height */}
      <nav style={{ height: 48, borderBottom: "1px solid #1f2937", padding: "0 24px", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={() => router.push("/history")} style={{ color: "#9ca3af", fontSize: 14, background: "none", border: "none", cursor: "pointer" }}>
            ← Mindmaps cũ
          </button>
          {data && <span style={{ color: "#374151" }}>|</span>}
          {data && <span style={{ color: "#d1d5db", fontSize: 14, fontWeight: 600 }}>{title}</span>}
        </div>

        {data && (
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: "#6b7280" }}>
              🔵 {nodes.length} nodes · 🔗 {edges.length} edges · depth {stats.depth}
            </span>
            <button
              onClick={() => downloadMindmapJSON(id, title)}
              style={{ fontSize: 12, background: "#1f2937", color: "#d1d5db", border: "none", padding: "6px 12px", borderRadius: 8, cursor: "pointer" }}
            >
              ⬇ JSON
            </button>
            <button
              onClick={() => router.push("/")}
              style={{ fontSize: 12, background: "#2563eb", color: "white", border: "none", padding: "6px 12px", borderRadius: 8, cursor: "pointer" }}
            >
              + Tạo mới
            </button>
          </div>
        )}
      </nav>

      {/* Canvas — flex-1 để chiếm toàn bộ phần còn lại */}
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        {loading && (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 40, height: 40, border: "4px solid #3b82f6", borderTopColor: "transparent", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
          </div>
        )}

        {error && (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <p style={{ color: "#f87171" }}>Lỗi: {error}</p>
          </div>
        )}

        {data && nodes.length > 0 && (
          <MindMap nodes={nodes} edges={edges} stats={stats} title={title} />
        )}

        {data && nodes.length === 0 && !loading && (
          <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <p style={{ color: "#6b7280" }}>Không có dữ liệu để hiển thị</p>
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
