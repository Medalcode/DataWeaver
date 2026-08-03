from pathlib import Path
from scripts.graphify import CodebaseGraphBuilder, generate_graph_report


def test_graphify_builder():
    backend_dir = Path(__file__).resolve().parent.parent / "backend" / "app"
    builder = CodebaseGraphBuilder(backend_dir)
    graph_data = builder.build()

    assert "metadata" in graph_data
    assert graph_data["metadata"]["project"] == "DataWeaver"
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["edges"]) > 0

    report = generate_graph_report(graph_data)
    assert "# DataWeaver Architecture Graphify Report" in report
