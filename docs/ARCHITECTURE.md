# Architecture Overview

## System Design Philosophy

Macro Builder is designed around three core principles:

1. **Separation of Concerns** - UI, business logic, and execution are decoupled
2. **Declarative Configuration** - Workflows are data, not code
3. **Multi-Tenant by Design** - Company isolation built into every layer

## Component Architecture

```
┌───────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                  │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │   Auth   │  │ Workflow │  │    Execution       │  │
│  │  Routes  │  │  Routes  │  │     Routes         │  │
│  └──────────┘  └──────────┘  └────────────────────┘  │
└───────────────────┬───────────────────────────────────┘
                    │
┌───────────────────┴───────────────────────────────────┐
│             Business Logic Layer                       │
│  ┌───────────────────────────────────────────────┐   │
│  │          Rule Engine (Stateless)               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │  Filter  │  │   Move   │  │ GroupSum │    │   │
│  │  │   Rule   │  │   Rule   │  │   Rule   │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘    │   │
│  │         Factory Pattern + Command Pattern     │   │
│  └───────────────────────────────────────────────┘   │
└───────────────────┬───────────────────────────────────┘
                    │
┌───────────────────┴───────────────────────────────────┐
│              Persistence Layer                         │
│  ┌──────────────┐              ┌──────────────┐      │
│  │  PostgreSQL  │              │  File System │      │
│  │  (Metadata)  │              │   (Temp)     │      │
│  └──────────────┘              └──────────────┘      │
└────────────────────────────────────────────────────────┘

        ┌───────────────────────────────┐
        │   Async Processing Layer      │
        │  ┌──────────┐  ┌──────────┐  │
        │  │  Celery  │  │  Redis   │  │
        │  │  Worker  │  │  Broker  │  │
        │  └──────────┘  └──────────┘  │
        └───────────────────────────────┘
```

## Data Flow

### Workflow Execution Flow

1. **Client Request**  
   → POST /executions with `workflow_version_id` and `file_id`

2. **API Validation**  
   → Verify workflow and file exist  
   → Check user authorization

3. **Execution Record Created**  
   → Status: `pending`  
   → Stored in PostgreSQL

4. **Celery Task Dispatched**  
   → Async task queued in Redis  
   → API returns execution ID immediately

5. **Worker Processes Task**  
   → Load Excel file into DataFrame  
   → Execute workflow steps sequentially  
   → Generate output files

6. **Results Persisted**  
   → Execution logs saved  
   → Output files linked  
   → Status updated to `success` or `failed`

7. **Client Polls Status**  
   → GET /executions/{id}  
   → Download output when complete

### Workflow Definition Lifecycle

```
Create Workflow
     ↓
Save Version 1 (rules JSON)
     ↓
Edit Rules
     ↓
Save Version 2 (immutable)
     ↓
Execute Version 2
     ↓
Version 1 still available
```

**Key Insight**: Versions are immutable. Edits create new versions. This enables:
- Rollback to previous versions
- Audit trail
- Reproducible executions

## Design Patterns Used

### 1. Command Pattern
Each rule is a command object that encapsulates an action.

```python
class Rule(ABC):
    @abstractmethod
    def execute(self, context, params):
        pass
```

**Benefits**:
- New rules added without changing engine code
- Rules are testable in isolation
- Easy to compose complex workflows

### 2. Factory Pattern
Rule instantiation abstracted to a factory.

```python
RULE_REGISTRY = {
    "filter": FilterRule,
    "move": MoveRule,
    ...
}

def get_rule(type): 
    return RULE_REGISTRY[type]()
```

**Benefits**:
- Centralized rule registration
- Type validation
- Extensibility

### 3. Strategy Pattern
Execution context carries state; rules modify it.

```python
context = ExecutionContext(dataframe)
for step in workflow:
    rule.execute(context, step.params)
```

**Benefits**:
- Rules don't need to know about each other
- Shared state management
- Simplified testing

## Multi-Tenancy Architecture

### Tenant Isolation Strategy

**Every resource** has a `company_id`:

```sql
SELECT * FROM workflows 
WHERE company_id = :current_company_id
```

### Security Model

```
User ──has─→ Membership ──in─→ Company
              (role)

Company owns:
  - Workflows
  - Files
  - Executions
```

**Authorization Check**:
```python
if resource.company_id != current_user.company_id:
    raise HTTP403
```

## Scalability Considerations

### Horizontal Scaling

- **API Servers**: Stateless, can run N instances behind load balancer
- **Celery Workers**: Add more workers for parallel execution
- **Database**: PostgreSQL read replicas for queries

### File Storage Strategy

**Current**: Local file system  
**Production**: S3-compatible object storage (MinIO, AWS S3)

**File Lifecycle**:
1. Upload → Temp storage
2. Execution → Read from storage
3. Output → Temp storage
4. Expiration (24h) → Auto-delete

### Database Optimization

**Indexes**:
- `workflows.company_id`
- `executions.company_id`
- `execution_logs.execution_id`
- `users.email`

**Performance Queries**:
- Always filter by `company_id` first
- Pagination on list endpoints
- Eager loading of relationships

## Extension Points

### Adding New Rules

1. Create `app/engine/rules/my_rule.py`
```python
from app.engine.rules.base import Rule

class MyRule(Rule):
    def execute(self, context, params):
        # implement logic
        pass
```

2. Register in factory
```python
RULE_REGISTRY["my_rule"] = MyRule
```

3. Document in API schema

### Adding New Operators (Filter Rule)

Edit `app/engine/rules/filter.py`:
```python
elif operator == "my_operator":
    mask = custom_logic(df[column], value)
```

### Custom Authentication

Replace `app/auth.py` functions:
- `get_current_user()` - SSO integration
- `create_access_token()` - OAuth2

## Technology Choices

| Decision | Reasoning |
|----------|-----------|
| **FastAPI** | Async support, auto docs, Pydantic validation |
| **SQLAlchemy** | ORM flexibility, migration support |
| **Celery** | Industry standard for Python async tasks |
| **Pandas** | Excel processing powerhouse |
| **PostgreSQL** | JSONB for rules, strong consistency |

## Security Architecture

### Authentication
- JWT with HS256 signing
- Tokens expire after 30 minutes
- Stored in Authorization header

### Authorization
- Company-level isolation
- Role-based access (future)
- Resource ownership checks

### Data Protection
- Passwords hashed with bcrypt
- Files auto-expire
- No sensitive data in logs

## Monitoring & Observability

### Recommended Additions

- **Metrics**: Prometheus + Grafana
  - Execution duration
  - Success/failure rates
  - Queue length

- **Logging**: Structured JSON logs
  - Request IDs
  - User context
  - Performance traces

- **Alerting**: 
  - Failed executions > threshold
  - Queue backup
  - Database connection pool exhaustion

---

**Last Updated**: 2024-01-01
