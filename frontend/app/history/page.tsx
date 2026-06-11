"use client";
// app/history/page.tsx — Trang "Mindmaps cũ"

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import MindmapCard from "@/components/MindmapCard";
import {
  listSavedMindmaps,
  deleteSavedMindmap,
  downloadMindmapJSON,
} from "@/services/api";

export default function HistoryPage() {
  const router  = useRouter();
  const [items,   setItems]   = useState<any[]>([]);
  const [total,   setTotal]   = useState(0);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [page,    setPage]    = useState(0);
  const LIMIT = 12;

  async function load(p: number = 0) {
    setLoading(true);
    setError(null);
    try {
      const data = await listSavedMindmaps(p * LIMIT, LIMIT);
      setItems(data.items);
      setTotal(data.total);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(page); }, [page]);

  function handleOpen(id: string) {
    router.push(`/mindmap/${id}`);
  }

  async function handleDelete(id: string) {
    try {
      await deleteSavedMindmap(id);
      load(page);
    } catch {
      alert("Lỗi xoá mindmap");
    }
  }

  function handleDownload(id: string) {
    const item = items.find(i => i.id === id);
    downloadMindmapJSON(id, item?.title || "mindmap");
  }

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navbar */}
      <nav className="border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg">AI Mindmap</span>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => router.push("/")}
            className="text-sm text-gray-400 hover:text-white transition"
          >
            + Tạo mới
          </button>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">Mindmaps đã lưu</h1>
            <p className="text-gray-400 text-sm mt-1">{total} mindmap</p>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-red-400 bg-red-900/20 rounded-xl p-4 text-sm">{error}</div>
        )}

        {/* Empty state */}
        {!loading && !error && items.length === 0 && (
          <div className="text-center py-20">
            <span className="text-6xl opacity-20">🧠</span>
            <p className="text-gray-500 mt-4">Chưa có mindmap nào được lưu</p>
            <button
              onClick={() => router.push("/")}
              className="mt-4 bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-xl text-sm font-semibold transition"
            >
              Tạo mindmap đầu tiên
            </button>
          </div>
        )}

        {/* Grid */}
        {!loading && items.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {items.map((item) => (
                <MindmapCard
                  key={item.id}
                  mindmap={item}
                  onOpen={handleOpen}
                  onDelete={handleDelete}
                  onDownload={handleDownload}
                />
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(p => Math.max(0, p-1))}
                  disabled={page === 0}
                  className="px-4 py-2 bg-gray-800 rounded-lg text-sm disabled:opacity-40"
                >
                  ← Trước
                </button>
                <span className="text-gray-400 text-sm">
                  {page+1} / {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages-1, p+1))}
                  disabled={page >= totalPages-1}
                  className="px-4 py-2 bg-gray-800 rounded-lg text-sm disabled:opacity-40"
                >
                  Sau →
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
