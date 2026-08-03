"""
Graphify Knowledge Graph Generator for DataWeaver.

Parses the codebase AST, models, API routes, Celery tasks, and engine rules
to build a persistent, queryable Knowledge Graph (graph.json), an interactive
visualization (graph.html), and an architecture report (GRAPH_REPORT.md).
"""

import ast
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend" / "app"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "graphify"


class CodebaseGraphBuilder:
    def __init__(self, backend_path: Path):
        self.backend_path = backend_path
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self._node_ids: set[str] = set()

    def add_node(
        self,
        node_id: str,
        label: str,
        kind: str,
        layer: str,
        details: dict[str, Any] | None = None,
    ):
        if node_id not in self._node_ids:
            self._node_ids.add(node_id)
            self.nodes.append(
                {
                    "id": node_id,
                    "label": label,
                    "kind": kind,  # module, class, function, endpoint, task, model, rule
                    "layer": layer,  # api, core, engine, tasks
                    "details": details or {},
                }
            )

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        details: dict[str, Any] | None = None,
    ):
        if source in self._node_ids and target in self._node_ids:
            self.edges.append(
                {
                    "source": source,
                    "target": target,
                    "relation": relation,  # IMPORTS, CALLS, CALLS_TASK, DEFINES_MODEL, DEFINES_RULE, USES_SCHEMA
                    "details": details or {},
                }
            )

    def build(self) -> dict[str, Any]:
        print(f"[Graphify] Analyzing codebase under {self.backend_path}...")
        py_files = list(self.backend_path.rglob("*.py"))

        # Step 1: Discover modules and AST constructs
        for file_path in py_files:
            rel_path = file_path.relative_to(self.backend_path)
            module_name = "app." + ".".join(rel_path.with_suffix("").parts)
            layer = rel_path.parts[0] if rel_path.parts else "root"

            self.add_node(
                node_id=module_name,
                label=rel_path.name,
                kind="module",
                layer=layer,
                details={"file_path": str(rel_path)},
            )

            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(file_path))
                self._inspect_ast(module_name, layer, tree)
            except Exception as e:
                print(f"[Graphify Warning] Error parsing {file_path}: {e}")

        # Step 2: Establish cross-module import and reference edges
        self._build_references(py_files)

        return {
            "metadata": {
                "project": "DataWeaver",
                "version": "1.1.0",
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "layers": list({n["layer"] for n in self.nodes}),
            },
            "nodes": self.nodes,
            "edges": self.edges,
        }

    def _inspect_ast(self, module_name: str, layer: str, tree: ast.AST):
        for stmt in tree.body if isinstance(tree, ast.Module) else []:
            if isinstance(stmt, ast.ClassDef):
                class_id = f"{module_name}.{stmt.name}"
                is_model = any(
                    isinstance(base, ast.Name) and base.id == "Base"
                    for base in stmt.bases
                )
                is_rule = any(
                    isinstance(base, ast.Name) and base.id == "Rule"
                    for base in stmt.bases
                )

                kind = "model" if is_model else ("rule" if is_rule else "class")
                self.add_node(
                    node_id=class_id,
                    label=stmt.name,
                    kind=kind,
                    layer=layer,
                    details={"docstring": ast.get_docstring(stmt) or ""},
                )
                self.add_edge(module_name, class_id, "CONTAINS")

            elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                func_id = f"{module_name}.{stmt.name}"
                is_endpoint = False
                is_task = False

                for decorator in stmt.decorator_list:
                    dec_name = ""
                    if isinstance(decorator, ast.Call):
                        decorator = decorator.func
                    if isinstance(decorator, ast.Attribute):
                        dec_name = decorator.attr
                    elif isinstance(decorator, ast.Name):
                        dec_name = decorator.id

                    if dec_name in ("get", "post", "put", "delete", "patch"):
                        is_endpoint = True
                    elif dec_name == "task":
                        is_task = True

                kind = "endpoint" if is_endpoint else ("task" if is_task else "function")
                self.add_node(
                    node_id=func_id,
                    label=stmt.name,
                    kind=kind,
                    layer=layer,
                    details={"is_async": isinstance(stmt, ast.AsyncFunctionDef)},
                )
                self.add_edge(module_name, func_id, "CONTAINS")

    def _build_references(self, py_files: list[Path]):
        for file_path in py_files:
            rel_path = file_path.relative_to(self.backend_path)
            source_module = "app." + ".".join(rel_path.with_suffix("").parts)

            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        target_mod = (
                            node.module
                            if node.module.startswith("app")
                            else f"app.{node.module}"
                        )
                        if target_mod in self._node_ids:
                            self.add_edge(source_module, target_mod, "IMPORTS")
                        for alias in node.names:
                            target_entity = f"{target_mod}.{alias.name}"
                            if target_entity in self._node_ids:
                                self.add_edge(source_module, target_entity, "USES")

                    elif isinstance(node, ast.Call):
                        func_name = ""
                        if isinstance(node.func, ast.Attribute):
                            func_name = node.func.attr
                        elif isinstance(node.func, ast.Name):
                            func_name = node.func.id

                        if func_name in ("delay", "apply_async"):
                            for target_node in self.nodes:
                                if target_node["kind"] == "task":
                                    self.add_edge(
                                        source_module,
                                        target_node["id"],
                                        "DISPATCHES_TASK",
                                    )
            except Exception:
                pass


def generate_graph_html(graph_data: dict[str, Any]) -> str:
    """Generates an interactive HTML/JS visualization using Vis.js Graph library."""

    layer_colors = {
        "api": "#009688",
        "core": "#3F51B5",
        "engine": "#FF9800",
        "tasks": "#9C27B0",
        "rules": "#4CAF50",
        "root": "#607D8B",
    }

    vis_nodes = []
    for node in graph_data["nodes"]:
        color = layer_colors.get(node["layer"], "#795548")
        shape = (
            "hexagon"
            if node["kind"] == "endpoint"
            else ("diamond" if node["kind"] == "task" else "dot")
        )
        vis_nodes.append(
            {
                "id": node["id"],
                "label": node["label"],
                "group": node["layer"],
                "title": f"<b>{node['id']}</b><br/>Type: {node['kind']}<br/>Layer: {node['layer']}",
                "color": {"background": color, "border": "#FFFFFF"},
                "shape": shape,
                "size": 18 if node["kind"] in ("endpoint", "task", "model") else 12,
            }
        )

    vis_edges = []
    for edge in graph_data["edges"]:
        vis_edges.append(
            {
                "from": edge["source"],
                "to": edge["target"],
                "label": edge["relation"],
                "arrows": "to",
                "font": {"size": 9, "align": "middle", "color": "#999999"},
                "color": {"color": "#666666", "highlight": "#2196F3"},
            }
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataWeaver Architecture Knowledge Graph (Graphify)</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        header {{
            background-color: #161b22;
            padding: 14px 24px;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        h1 {{ font-size: 1.25rem; color: #58a6ff; font-weight: 600; }}
        .badge {{
            background-color: #21262d;
            border: 1px solid #30363d;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            color: #8b949e;
        }}
        #main-container {{
            display: flex;
            flex: 1;
            position: relative;
        }}
        #mynetwork {{
            flex: 1;
            height: 100%;
            background-color: #0d1117;
        }}
        #sidebar {{
            width: 320px;
            background-color: #161b22;
            border-left: 1px solid #30363d;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            font-size: 0.9rem;
        }}
        .sidebar-card {{
            background-color: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 12px;
        }}
        .sidebar-card h3 {{ font-size: 0.95rem; margin-bottom: 8px; color: #58a6ff; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.85rem; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
    </style>
</head>
<body>
    <header>
        <h1>DataWeaver Knowledge Graph (Graphify)</h1>
        <div class="badge">Nodes: {len(vis_nodes)} | Edges: {len(vis_edges)} | Engine: AST Parser</div>
    </header>
    <div id="main-container">
        <div id="mynetwork"></div>
        <div id="sidebar">
            <div class="sidebar-card">
                <h3>Architecture Layers</h3>
                <div class="legend-item"><span class="legend-color" style="background: #009688;"></span> API Layer (Gateway)</div>
                <div class="legend-item"><span class="legend-color" style="background: #3F51B5;"></span> Core / Data / Auth</div>
                <div class="legend-item"><span class="legend-color" style="background: #FF9800;"></span> Engine & Rule Execution</div>
                <div class="legend-item"><span class="legend-color" style="background: #9C27B0;"></span> Celery Tasks (Workers)</div>
                <div class="legend-item"><span class="legend-color" style="background: #4CAF50;"></span> Parametric Rules</div>
            </div>
            <div class="sidebar-card">
                <h3>Node Inspector</h3>
                <div id="node-info"><i>Click any node in the graph to inspect connections and metadata.</i></div>
            </div>
        </div>
    </div>
    <script type="text/javascript">
        const nodes = new vis.DataSet({json.dumps(vis_nodes)});
        const edges = new vis.DataSet({json.dumps(vis_edges)});
        const container = document.getElementById('mynetwork');
        const data = {{ nodes: nodes, edges: edges }};
        const options = {{
            nodes: {{
                font: {{ color: '#c9d1d9', size: 12 }},
                borderWidth: 2
            }},
            edges: {{
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                stabilization: true,
                barnesHut: {{ gravConstant: -3000, springLength: 95 }}
            }},
            interaction: {{ hover: true, tooltipDelay: 200 }}
        }};
        const network = new vis.Network(container, data, options);

        network.on("selectNode", function (params) {{
            const nodeId = params.nodes[0];
            const selectedNode = nodes.get(nodeId);
            document.getElementById('node-info').innerHTML = `
                <b>ID:</b> ${{selectedNode.id}}<br/>
                <b>Label:</b> ${{selectedNode.label}}<br/>
                <b>Group/Layer:</b> ${{selectedNode.group}}<br/>
            `;
        }});
    </script>
</body>
</html>
"""
    return html_content


def generate_graph_report(graph_data: dict[str, Any]) -> str:
    """Generates GRAPH_REPORT.md markdown report from graph analytical data."""

    nodes_by_kind: dict[str, int] = {}
    nodes_by_layer: dict[str, int] = {}

    for node in graph_data["nodes"]:
        k = node["kind"]
        l = node["layer"]
        nodes_by_kind[k] = nodes_by_kind.get(k, 0) + 1
        nodes_by_layer[l] = nodes_by_layer.get(l, 0) + 1

    report = f"""# DataWeaver Architecture Graphify Report 📊

**Generated Version**: {graph_data['metadata']['version']}  
**Total Nodes**: {graph_data['metadata']['total_nodes']}  
**Total Edges**: {graph_data['metadata']['total_edges']}  

---

## 🏗️ Architecture Breakdown

### Nodes by Component Kind

| Component Kind | Count | Description |
|----------------|-------|-------------|
| **Module** | {nodes_by_kind.get('module', 0)} | Python files and package boundaries |
| **Function / Endpoint** | {nodes_by_kind.get('function', 0) + nodes_by_kind.get('endpoint', 0)} | REST endpoints and internal utilities |
| **Class / Model** | {nodes_by_kind.get('class', 0) + nodes_by_kind.get('model', 0)} | ORM entities and domain data structures |
| **Task** | {nodes_by_kind.get('task', 0)} | Celery asynchronous worker tasks |
| **Rule** | {nodes_by_kind.get('rule', 0)} | Parametric transformation rules |

### Nodes by Architectural Layer

| Layer | Nodes Count | Primary Responsibility |
|-------|-------------|------------------------|
| `api` | {nodes_by_layer.get('api', 0)} | FastAPI Routers and Request Handling |
| `core` | {nodes_by_layer.get('core', 0)} | Database Models, Auth, Schemas & Config |
| `engine` | {nodes_by_layer.get('engine', 0)} | Rule Execution Runtime & Polymorphic Engine |
| `tasks` | {nodes_by_layer.get('tasks', 0)} | Celery Asynchronous Workers & Maintenance |

---

## 🔗 Key Architectural Connections

* **Gateway → Tasks**: API Endpoints dispatch asynchronous workflows via `execute_workflow_task.delay()`.
* **Tasks → Engine**: Worker tasks instantiate `RuleEngine` to execute transformation steps.
* **Engine → Rules**: `RuleEngine` delegates step evaluation to `RULE_REGISTRY` (`FilterRule`, `AggregateRule`, `MoveRule`).
* **Core → Infrastructure**: ORM models interface directly with PostgreSQL metadata tables.

---

## 🖼️ Interactive Visualization

To explore the live interactive node topology, open:
[`docs/graphify/graph.html`](graph.html)
"""
    return report


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    builder = CodebaseGraphBuilder(BACKEND_DIR)
    graph_data = builder.build()

    # 1. Save graph.json
    json_path = OUTPUT_DIR / "graph.json"
    json_path.write_text(json.dumps(graph_data, indent=2), encoding="utf-8")
    print(f"[Graphify] Saved Knowledge Graph to {json_path}")

    # 2. Save graph.html
    html_path = OUTPUT_DIR / "graph.html"
    html_path.write_text(generate_graph_html(graph_data), encoding="utf-8")
    print(f"[Graphify] Saved Interactive Visualization to {html_path}")

    # 3. Save GRAPH_REPORT.md
    report_path = OUTPUT_DIR / "GRAPH_REPORT.md"
    report_path.write_text(generate_graph_report(graph_data), encoding="utf-8")
    print(f"[Graphify] Saved Graphify Report to {report_path}")


if __name__ == "__main__":
    main()
