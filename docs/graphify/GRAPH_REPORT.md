# DataWeaver Architecture Graphify Report 📊

**Generated Version**: 1.1.0  
**Total Nodes**: 91  
**Total Edges**: 190  

---

## 🏗️ Architecture Breakdown

### Nodes by Component Kind

| Component Kind | Count | Description |
|----------------|-------|-------------|
| **Module** | 28 | Python files and package boundaries |
| **Function / Endpoint** | 28 | REST endpoints and internal utilities |
| **Class / Model** | 30 | ORM entities and domain data structures |
| **Task** | 2 | Celery asynchronous worker tasks |
| **Rule** | 3 | Parametric transformation rules |

### Nodes by Architectural Layer

| Layer | Nodes Count | Primary Responsibility |
|-------|-------------|------------------------|
| `api` | 26 | FastAPI Routers and Request Handling |
| `core` | 37 | Database Models, Auth, Schemas & Config |
| `engine` | 20 | Rule Execution Runtime & Polymorphic Engine |
| `tasks` | 5 | Celery Asynchronous Workers & Maintenance |

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
