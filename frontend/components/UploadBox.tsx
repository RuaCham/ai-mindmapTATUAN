"use client";
// components/UploadBox.tsx

import { useCallback, useState } from "react";
import { UploadResponse } from "@/types";
import { uploadPDF } from "@/services/api";

interface Props {
  onUploaded: (res: UploadResponse) => void;
}

export default function UploadBox({ onUploaded }: Props) {
  const [dragging,  setDragging]  = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.endsWith(".pdf")) {
      setError("Chỉ chấp nhận file PDF");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const res = await uploadPDF(file);
      onUploaded(res);
    } catch (e: any) {
      setError(e.message || "Upload thất bại");
    } finally {
      setUploading(false);
    }
  }, [onUploaded]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`
        relative flex flex-col items-center justify-center
        w-full h-56 rounded-2xl border-2 border-dashed
        transition-all duration-200 cursor-pointer
        ${dragging
          ? "border-blue-500 bg-blue-500/10"
          : "border-gray-600 bg-gray-800/50 hover:border-gray-400"}
      `}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={onInputChange}
        className="absolute inset-0 opacity-0 cursor-pointer"
        disabled={uploading}
      />

      {uploading ? (
        <>
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-gray-400 text-sm">Đang upload...</p>
        </>
      ) : (
        <>
          <span className="text-5xl mb-3">📄</span>
          <p className="text-gray-300 font-medium">Kéo thả PDF vào đây</p>
          <p className="text-gray-500 text-sm mt-1">hoặc click để chọn file</p>
        </>
      )}

      {error && (
        <p className="absolute bottom-3 text-red-400 text-sm">{error}</p>
      )}
    </div>
  );
}
