// types/index.ts

export interface NodeData {
  label:    string;
  keywords: string[];
  summary:  string;
  depth:    number;
}

export interface FlowNode {
  id:       string;
  type:     "root" | "branch" | "leaf";
  data:     NodeData;
  position: { x: number; y: number };
}

export interface FlowEdge {
  id:     string;
  source: string;
  target: string;
  type:   string;
}

export interface MindmapStats {
  total_nodes: number;
  total_edges: number;
  depth:       number;
  keywords:    string[];
}

export interface MindmapResponse {
  title: string;
  nodes: FlowNode[];
  edges: FlowEdge[];
  stats: MindmapStats;
}

export interface UploadResponse {
  id:        string;
  filename:  string;
  num_pages: number;
  num_chars: number;
  preview:   string;
}
