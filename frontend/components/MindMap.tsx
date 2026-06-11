"use client";
// components/MindMap.tsx

import { useCallback, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { FlowNode, FlowEdge, MindmapStats } from "@/types";
import { applyDagreLayout } from "@/lib/layout";
import { RootNode, BranchNode, LeafNode } from "./NodeCard";

const nodeTypes = {
  root:   RootNode,
  branch: BranchNode,
  leaf:   LeafNode,
};

interface Props {
  nodes:  FlowNode[];
  edges:  FlowEdge[];
  stats:  MindmapStats;
  title:  string;
}

function Flow({ nodes: rawNodes, edges: rawEdges, stats, title }: Props) {
  const layoutedNodes = applyDagreLayout(rawNodes, rawEdges, "LR");

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes as any);
  const [edges, setEdges, onEdgesChange] = useEdgesState(rawEdges as any);

  // Re-layout khi data thay đổi
  useEffect(() => {
    const ln = applyDagreLayout(rawNodes, rawEdges, "LR");
    setNodes(ln as any);
    setEdges(rawEdges as any);
  }, [rawNodes, rawEdges]);

  return (
    // width và height phải explicit — React Flow cần biết kích thước
    <div style={{ width: "100%", height: "100%" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        style={{ background: "#0f1117" }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1f2937" />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            if (n.type === "root")   return "#3b82f6";
            if (n.type === "branch") return "#4b5563";
            return "#374151";
          }}
          style={{ background: "#1f2937" }}
        />
      </ReactFlow>
    </div>
  );
}

export default function MindMap(props: Props) {
  return (
    // ReactFlowProvider bắt buộc khi dùng ngoài context mặc định
    <ReactFlowProvider>
      <div style={{ width: "100%", height: "100%" }}>
        <Flow {...props} />
      </div>
    </ReactFlowProvider>
  );
}
