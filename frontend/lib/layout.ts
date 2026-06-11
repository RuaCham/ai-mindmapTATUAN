// lib/layout.ts
// Auto layout mindmap nodes dùng dagre

import dagre from "@dagrejs/dagre";
import { FlowNode, FlowEdge } from "@/types";

const NODE_WIDTH  = 180;
const NODE_HEIGHT = 60;

export function applyDagreLayout(
  nodes: FlowNode[],
  edges: FlowEdge[],
  direction: "TB" | "LR" = "LR",   // LR = Left→Right (mindmap style)
): FlowNode[] {
  const g = new dagre.graphlib.Graph();

  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir:  direction,
    ranksep:  80,   // khoảng cách giữa các cấp
    nodesep:  40,   // khoảng cách giữa các node cùng cấp
    marginx:  20,
    marginy:  20,
  });

  // Thêm nodes vào graph
  nodes.forEach((node) => {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  // Thêm edges
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  // Tính toán layout
  dagre.layout(g);

  // Cập nhật position cho từng node
  return nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - NODE_WIDTH  / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });
}
