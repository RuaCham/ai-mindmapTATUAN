"use client";
// components/NodeCard.tsx

import { Handle, Position, NodeProps } from "@xyflow/react";

interface NodeData {
  label:     string;
  keywords:  string[];
  summary:   string;
  main_idea: string;
  depth:     number;
}

// ── Root node ─────────────────────────────────────────────────────────────────
export function RootNode({ data }: NodeProps) {
  const d = data as unknown as NodeData;
  return (
    <div className="bg-blue-600 border-2 border-blue-400 rounded-2xl px-6 py-3 shadow-lg shadow-blue-500/20 max-w-[260px]">
      <p className="text-white font-bold text-sm leading-snug">{d.label}</p>
      <Handle type="source" position={Position.Right} className="!bg-blue-300" />
    </div>
  );
}

// ── Branch node (có children) ─────────────────────────────────────────────────
export function BranchNode({ data }: NodeProps) {
  const d = data as unknown as NodeData;
  return (
    <div className="bg-gray-800 border border-gray-600 rounded-xl px-4 py-3 shadow-md max-w-[240px]">
      <Handle type="target" position={Position.Left}  className="!bg-gray-500" />

      {/* Tiêu đề */}
      <p className="text-gray-100 font-semibold text-sm leading-snug mb-1">{d.label}</p>

      {/* Main idea — ý chính của section */}
      {d.main_idea && d.main_idea !== d.label && (
        <p className="text-gray-400 text-xs leading-relaxed mb-2 border-l-2 border-blue-500/50 pl-2">
          {d.main_idea.length > 80 ? d.main_idea.slice(0, 77) + "..." : d.main_idea}
        </p>
      )}

      {/* Keywords dạng tag */}
      {d.keywords && d.keywords.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {d.keywords.slice(0, 3).map((kw) => (
            <span key={kw} className="bg-gray-700 text-gray-400 text-[10px] px-2 py-0.5 rounded-full border border-gray-600">
              {kw.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      <Handle type="source" position={Position.Right} className="!bg-gray-500" />
    </div>
  );
}

// ── Leaf node (nội dung thật — bullet item hoặc câu tóm tắt) ─────────────────
export function LeafNode({ data }: NodeProps) {
  const d = data as unknown as NodeData;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 max-w-[200px]">
      <Handle type="target" position={Position.Left} className="!bg-gray-600" />
      <p className="text-gray-300 text-xs leading-relaxed">
        {d.label.length > 70 ? d.label.slice(0, 67) + "..." : d.label}
      </p>
    </div>
  );
}
