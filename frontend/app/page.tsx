"use client";
// app/page.tsx

import { useState } from "react";
import { useRouter } from "next/navigation";
import UploadBox from "@/components/UploadBox";
import MindMap   from "@/components/MindMap";
import { getMindmap, saveMindmap } from "@/services/api";
import { UploadResponse, MindmapResponse } from "@/types";

type Step = "idle" | "uploaded" | "loading" | "done" | "error";

export default function Home() {
  const router  = useRouter();
  const [step,      setStep]      = useState<Step>("idle");
  const [upload,    setUpload]    = useState<UploadResponse | null>(null);
  const [mindmap,   setMindmap]   = useState<MindmapResponse | null>(null);
  const [error,     setError]     = useState<string | null>(null);
  const [savedId,   setSavedId]   = useState<string | null>(null);
  const [saving,    setSaving]    = useState(false);

  const [maxKw,    setMaxKw]    = useState(15);
  const [topSents, setTopSents] = useState(5);
  const [nTopics,  setNTopics]  = useState(4);

  async function handleUploaded(res: UploadResponse) {
    setUpload(res);
    setStep("uploaded");
    setSavedId(null);
  }

  async function handleGenerate() {
    if (!upload) return;
    setStep("loading");
    setError(null);
    setSavedId(null);
    try {
      const result = await getMindmap(upload.id, maxKw, topSents, nTopics);
      setMindmap(result);
      setStep("done");
      // Auto-save sau khi generate xong
      await autoSave(result, upload);
    } catch (e: any) {
      setError(e.message);
      setStep("error");
    }
  }

  async function autoSave(result: MindmapResponse, up: UploadResponse) {
    setSaving(true);
    try {
      const saved = await saveMindmap({
        title:           result.title,
        source_pdf_name: up.filename,
        mindmap_data:    result,
        keywords:        Object.fromEntries(
                           (result.stats.keywords || []).map((k, i) => [k, 1 - i * 0.05])
                         ),
        num_pages:       up.num_pages,
      });
      setSavedId(saved.id);
    } catch {
      // Auto-save thất bại không block UI
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setStep("idle");
    setUpload(null);
    setMindmap(null);
    setError(null);
    setSavedId(null);
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Navbar */}
      <nav className="border-b border-gray-800 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-bold text-lg">AI Mindmap</span>
        </div>
        <div className="flex items-center gap-3">
          {saving && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <span className="w-3 h-3 border-2 border-gray-500 border-t-transparent rounded-full animate-spin inline-block" />
              Đang lưu...
            </span>
          )}
          {savedId && !saving && (
            <span className="text-xs text-green-400">✓ Đã lưu</span>
          )}
          <button
            onClick={() => router.push("/history")}
            className="text-sm text-gray-400 hover:text-white transition border border-gray-700 hover:border-gray-500 px-3 py-1.5 rounded-lg"
          >
            📋 Mindmaps cũ
          </button>
          {step !== "idle" && (
            <button onClick={handleReset} className="text-sm text-gray-400 hover:text-white transition">
              ← Tạo mới
            </button>
          )}
        </div>
      </nav>

      <main className="flex-1 flex">
        {/* Left panel */}
        <aside className="w-72 border-r border-gray-800 p-5 flex flex-col gap-5 shrink-0">

          {step === "idle" && (
            <>
              <h2 className="font-semibold text-gray-300">Upload PDF</h2>
              <UploadBox onUploaded={handleUploaded} />
              <p className="text-xs text-gray-500 text-center">PDF có text layer · Tiếng Việt / Anh</p>
            </>
          )}

          {(step === "uploaded" || step === "error") && upload && (
            <>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-xs text-gray-400 mb-1">File đã upload</p>
                <p className="font-medium text-sm truncate">{upload.filename}</p>
                <div className="flex gap-3 mt-2 text-xs text-gray-400">
                  <span>{upload.num_pages} trang</span>
                  <span>{(upload.num_chars / 1000).toFixed(1)}k ký tự</span>
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 space-y-4">
                <p className="text-xs text-gray-400 font-semibold">Cài đặt</p>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-gray-400">Từ khoá: {maxKw}</span>
                  <input type="range" min={5} max={30} value={maxKw} onChange={e => setMaxKw(+e.target.value)} className="accent-blue-500" />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-gray-400">Top câu: {topSents}</span>
                  <input type="range" min={3} max={15} value={topSents} onChange={e => setTopSents(+e.target.value)} className="accent-blue-500" />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-xs text-gray-400">Số topic: {nTopics}</span>
                  <input type="range" min={2} max={10} value={nTopics} onChange={e => setNTopics(+e.target.value)} className="accent-blue-500" />
                </label>
              </div>

              <button onClick={handleGenerate} className="bg-blue-600 hover:bg-blue-500 transition rounded-xl py-3 font-semibold">
                🚀 Tạo Mindmap
              </button>
              {error && <p className="text-red-400 text-xs bg-red-900/20 rounded-lg p-3">{error}</p>}
            </>
          )}

          {step === "loading" && (
            <div className="flex flex-col items-center gap-4 py-10">
              <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-400 text-sm text-center">
                Đang phân tích PDF...<br/>
                <span className="text-xs text-gray-600">TF-IDF · TextRank · Clustering</span>
              </p>
            </div>
          )}

          {step === "done" && mindmap && (
            <div className="space-y-3">
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-xs text-gray-400 font-semibold mb-2">Kết quả</p>
                <div className="grid grid-cols-2 gap-2 text-center">
                  {[["Nodes", mindmap.stats.total_nodes], ["Edges", mindmap.stats.total_edges],
                    ["Depth", mindmap.stats.depth], ["Keywords", mindmap.stats.keywords.length]
                  ].map(([label, val]) => (
                    <div key={label as string} className="bg-gray-700 rounded-lg py-2">
                      <p className="text-blue-400 font-bold">{val}</p>
                      <p className="text-gray-400 text-xs">{label}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-xs text-gray-400 font-semibold mb-2">Top keywords</p>
                <div className="flex flex-wrap gap-1">
                  {mindmap.stats.keywords.map((kw) => (
                    <span key={kw} className="bg-blue-900/40 border border-blue-700/50 text-blue-300 text-xs px-2 py-0.5 rounded-full">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {savedId && (
                <button
                  onClick={() => router.push(`/mindmap/${savedId}`)}
                  className="w-full border border-green-700 text-green-400 hover:bg-green-900/20 transition rounded-xl py-2 text-sm"
                >
                  ✓ Xem trong Mindmaps cũ
                </button>
              )}

              <button onClick={handleReset} className="w-full border border-gray-600 hover:border-gray-400 transition rounded-xl py-2 text-sm text-gray-400 hover:text-white">
                Upload file mới
              </button>
            </div>
          )}
        </aside>

        {/* Right: canvas */}
        <section className="flex-1 relative">
          {step === "idle" && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <span className="text-7xl opacity-20">🧠</span>
              <p className="text-gray-600">Upload PDF để bắt đầu</p>
              <button
                onClick={() => router.push("/history")}
                className="text-sm text-gray-500 hover:text-gray-300 underline transition"
              >
                Hoặc xem lại mindmaps đã tạo →
              </button>
            </div>
          )}
          {step === "done" && mindmap && (
            <MindMap nodes={mindmap.nodes} edges={mindmap.edges} stats={mindmap.stats} title={mindmap.title} />
          )}
          {step === "loading" && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-3">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-gray-500 text-sm">Đang xử lý pipeline NLP...</p>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
