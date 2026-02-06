# Macro Builder

> **Low-code Excel automation platform for business users**

Transform repetitive Excel tasks into automated workflows without writing VBA code. Define business rules visually and let the system handle the execution.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A.svg?style=flat&logo=celery)](https://docs.celeryq.dev)

**English** | [Español](README.es.md)

## 🎯 Problem Statement

Organizations face critical challenges with Excel automation:

- **Knowledge dependency**: Processes trapped in VBA macros known only to specific employees
- **Maintenance nightmare**: Small changes require complete macro rewrites
- **Business continuity risk**: When the "Excel person" leaves, automation stops
- **No auditability**: Black-box macros with zero transparency

## 💡 Solution

Macro Builder converts business logic into **declarative, versionable workflows** that anyone can create and maintain.

### Core Value Propositions

✅ **No coding required** - Visual rule builder with natural language descriptions  
✅ **Full auditability** - Every execution logged with step-by-step details  
✅ **Version control** - Track changes, rollback, and compare workflow versions  
✅ **Multi-tenant** - Secure company isolation with role-based access  
✅ **Scalable** - Async execution handles large files efficiently  

## 🏗️ Architecture

### System Design

```
┌─────────────┐
│   React UI  │ (Rule Builder)
└──────┬──────┘
       │ HTTPS/REST
┌──────┴──────────────────────────┐
│       FastAPI Backend            │
│  ┌────────────┐  ┌────────────┐ │
│  │    Auth    │  │  Workflow  │ │
│  │   (JWT)    │  │   Engine   │ │
│  └────────────┘  └────────────┘ │
└──────┬────────────────┬──────────┘
       │                │
┌──────┴──────┐  ┌──────┴──────┐
│ PostgreSQL  │  │   Celery    │
│  (Metadata) │  │  (Async)    │
└─────────────┘  └──────┬──────┘
                        │
                 ┌──────┴──────┐
                 │    Redis    │
                 └─────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Layer** | FastAPI | REST endpoints, validation, auth |
| **Rule Engine** | Python + Pandas | Workflow execution logic |
| **Task Queue** | Celery + Redis | Async job processing |
| **Database** | PostgreSQL | Multi-tenant data persistence |
| **Storage** | File system | Temporary Excel file storage |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker

```bash
# Clone repository
git clone https://github.com/Medalcode/DataWeaver.git
cd DataWeaver

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# Access API docs
open http://localhost:8000/docs
```

The API will be available at `http://localhost:8000`

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📖 API Usage

### 1. Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "secure_password",
    "company_name": "Acme Corp"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=user@company.com" \
  -F "password=secure_password"
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Upload Excel File

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@sales_data.xlsx"
```

Response shows available columns:
```json
{
  "file_id": "uuid",
  "filename": "sales_data.xlsx",
  "columns": ["Date", "Product", "Amount", "Status"]
}
```

### 4. Create Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Sales Report",
    "description": "Filter and aggregate sales data"
  }'
```

### 5. Create Workflow Version (Define Rules)

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/versions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": {
      "steps": [
        {
          "type": "filter",
          "column": "Status",
          "operator": "=",
          "value": "Approved"
        },
        {
          "type": "group_sum",
          "group_by": "Product",
          "field": "Amount",
          "target_sheet": "Product_Summary"
        }
      ]
    }
  }'
```

### 6. Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_version_id": "uuid",
    "file_id": "uuid"
  }'
```

### 7. Check Execution Status

```bash
curl -X GET http://localhost:8000/api/v1/executions/{execution_id} \
  -H "Authorization: Bearer {token}"
```

### 8. Download Results

```bash
curl -X GET http://localhost:8000/api/v1/executions/{execution_id}/output \
  -H "Authorization: Bearer {token}" \
  --output result.xlsx
```

## 🎨 Available Rules

| Rule Type | Description | Parameters |
|-----------|-------------|------------|
| `filter` | Filter rows by condition | `column`, `operator`, `value` |
| `move` | Move rows to new sheet | `target_sheet` |
| `group_sum` | Group and aggregate | `group_by`, `field`, `target_sheet` |

### Supported Operators

- `=` Equal
- `!=` Not equal
- `>` Greater than
- `<` Less than
- `>=` Greater or equal
- `<=` Less or equal
- `contains` Text contains

## 🗄️ Database Schema

### Multi-Tenant Architecture

```sql
companies
├── users (via memberships)
├── workflows
│   └── workflow_versions
│       └── executions
│           ├── execution_logs
│           └── execution_files
└── files
```

**Key Design Decisions:**

- ✅ Single database with `company_id` isolation
- ✅ Explicit versioning for reproducibility
- ✅ Audit trail via execution logs
- ✅ Automatic file expiration

## 🔐 Security Features

- **JWT Authentication** - Secure token-based auth
- **Tenant Isolation** - Strict `company_id` filtering
- **Password Hashing** - Bcrypt with salt
- **File Expiration** - Automatic cleanup after 24h
- **Input Validation** - Pydantic schemas on all endpoints

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Test specific module
pytest tests/test_engine.py -v
```

## 📦 Project Structure

```
dataweaver/
├── backend/
│   └── app/
│       ├── engine/          # Rule execution engine
│       │   ├── context.py   # Execution state
│       │   ├── engine.py    # Main orchestrator
│       │   ├── validator.py # Pre-execution validation
│       │   └── rules/       # Rule implementations
│       │       ├── base.py
│       │       ├── filter.py
│       │       ├── move.py
│       │       ├── group_sum.py
│       │       └── factory.py
│       ├── routes/          # API endpoints
│       │   ├── auth.py
│       │   ├── workflows.py
│       │   ├── files.py
│       │   └── executions.py
│       ├── tasks/           # Celery tasks
│       │   └── workflow_execution.py
│       ├── models.py        # SQLAlchemy models
│       ├── schemas.py       # Pydantic schemas
│       ├── database.py      # DB connection
│       ├── auth.py          # Authentication logic
│       ├── config.py        # Application settings
│       └── main.py          # FastAPI app
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🎯 Roadmap

### MVP (Current)
- [x] Core rule engine (Filter, Move, GroupSum)
- [x] Multi-tenant architecture
- [x] Async execution
- [x] JWT authentication
- [x] File upload/download
- [x] Workflow versioning

### v2 (Planned)
- [ ] Additional rules (Sort, Transform, Validate)
- [ ] Multi-file workflows
- [ ] Scheduled executions
- [ ] Email notifications
- [ ] Execution history dashboard

### v3 (Future)
- [ ] React frontend (Rule Builder UI)
- [ ] Workflow marketplace
- [ ] API integrations (Google Sheets, Airtable)
- [ ] Custom rule development SDK
- [ ] Enterprise SSO

## 💼 Use Cases

### 1. Monthly Financial Reports
**Problem**: Finance team manually consolidates sales data from 10 branches  
**Solution**: Filter by date → Group by branch → Sum revenue → Export summary

### 2. Customer Data Cleanup
**Problem**: CRM exports contain duplicates and invalid emails  
**Solution**: Filter nulls → Remove duplicates → Validate emails → Flag issues

### 3. Inventory Reordering
**Problem**: Manual check of stock levels across warehouses  
**Solution**: Filter low stock → Group by supplier → Generate purchase orders

## 🤝 Contributing

Contributions welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-rule`)
3. Commit changes (`git commit -m 'Add amazing rule'`)
4. Push to branch (`git push origin feature/amazing-rule`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙋 Support

- **Documentation**: [docs.macrobuilder.io](https://docs.macrobuilder.io) (coming soon)
- **Issues**: [GitHub Issues](https://github.com/Medalcode/DataWeaver/issues)
- **Repository**: [GitHub](https://github.com/Medalcode/DataWeaver)

---

**Built with ❤️ for business users who deserve better than VBA**
