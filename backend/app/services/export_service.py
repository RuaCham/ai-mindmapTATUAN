# services/export_service.py
# Convert tree Node → JSON cho React Flow

from app.services.hierarchy_service import Node


def export_to_json(root: Node, title: str = "Document", keywords: dict = {}) -> dict:
    root.title = title
    nodes = []
    edges = []
    _traverse(root, nodes, edges, parent_id=None, depth=0)

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "depth":       _max_depth(root),
        "keywords":    list(keywords.keys())[:10],
    }

    return {"title": title, "nodes": nodes, "edges": edges, "stats": stats}


def _traverse(node: Node, nodes: list, edges: list, parent_id, depth: int):
    node_id   = node.id
    node_type = "root" if depth == 0 else ("leaf" if not node.children else "branch")

    nodes.append({
        "id":   node_id,
        "type": node_type,
        "data": {
            "label":     node.title,
            "keywords":  node.keywords,
            "summary":   node.summary,
            "main_idea": getattr(node, "main_idea", ""),
            "depth":     depth,
        },
        "position": {"x": 0, "y": 0},
    })

    if parent_id is not None:
        edges.append({
            "id":     f"e_{parent_id}_{node_id}",
            "source": parent_id,
            "target": node_id,
            "type":   "smoothstep",
        })

    for child in node.children:
        _traverse(child, nodes, edges, parent_id=node_id, depth=depth+1)


def _max_depth(node: Node, current: int = 0) -> int:
    if not node.children:
        return current
    return max(_max_depth(c, current+1) for c in node.children)
