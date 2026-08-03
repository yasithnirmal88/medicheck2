# Developer Guide

## Getting Started

### Setup

```bash
# Clone
git clone https://github.com/your-org/medicheck.git
cd medicheck

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # Configure as needed

# Run tests
py -3 -m pytest tests/ -v

# Start development server
uvicorn app.main:create_app --factory --reload --port 8000
```

### Code Organization

```
backend/
├── app/
│   ├── api/                     # Presentation layer
│   │   ├── v1/endpoints/        # HTTP endpoints
│   │   ├── v1/router.py         # Route registration
│   │   └── deps.py              # Dependency injection
│   ├── application/
│   │   └── services/            # Application services
│   ├── domain/
│   │   ├── entities/            # Business entities (57)
│   │   └── repositories/        # Repository interfaces (18)
│   ├── infrastructure/
│   │   └── persistence/
│   │       ├── models/          # ORM models (84)
│   │       └── repositories/    # SQL implementations (24)
│   └── modules/
│       └── questionnaire/       # Questionnaire engine
├── tests/
└── alembic/                     # Database migrations
```

## Architecture Rules

1. **Dependency Direction**: `api → application → domain ← infrastructure`
2. **Domain has zero imports** from other layers
3. **Application services** depend on abstract repository interfaces only
4. **Infrastructure** implements domain interfaces
5. **Entities** are plain `@dataclass` objects with business methods
6. **ORM models** are SQLAlchemy `Mapped` classes, separate from entities

## Adding a New Entity

1. Create domain entity in `domain/entities/` (`@dataclass`)
2. Create abstract repository in `domain/repositories/` (`ABC`)
3. Create ORM model in `infrastructure/persistence/models/` (extends `BaseModel`)
4. Create SQL repository in `infrastructure/persistence/repositories/`
5. Add service logic in `application/services/`
6. Add endpoint in `api/v1/endpoints/`
7. Register in `api/v1/router.py`
8. Write tests in `tests/`

## Testing

```bash
# Run all tests
py -3 -m pytest -v

# Run with coverage
py -3 -m pytest --cov=app tests/ -v

# Run specific test
py -3 -m pytest tests/test_uat.py -k "patient"

# UAT test suite (11 tests, 7 workflows)
py -3 -m pytest tests/test_uat.py -v
```

### Test Database

Tests use SQLite via `aiosqlite` (configured in `conftest.py`). Each test gets a fresh database session.

## Key Patterns

### Repository Pattern

```python
# Domain interface (domain/repositories/)
class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> User | None: ...

# Implementation (infrastructure/)
class SQLUserRepository(UserRepository):
    async def find_by_id(self, id: str) -> User | None:
        q = select(UserModel).where(UserModel.id == id)
        r = await self.session.execute(q)
        model = r.scalars().first()
        return self._to_entity(model) if model else None
```

### Service Pattern

```python
class SomeService:
    def __init__(self, repo: SomeRepository):
        self.repo = repo  # Depends on abstract interface

    async def do_something(self, data: dict):
        entity = self.repo.create(data)
        # Business logic
        return entity
```

### Dependency Injection (FastAPI)

```python
# api/deps.py
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

# api/v1/endpoints/something.py
@router.get("/items")
async def list_items(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = SomeService(SQLSomeRepository(db))
    return await svc.list()
```

## Coding Conventions

- **No comments** in code unless explaining non-obvious logic
- **Type hints** required on all function signatures
- **Async/await** throughout (no synchronous DB calls)
- **Datetime**: use `datetime.now(UTC)` (not `utcnow()`)
- **Error handling**: raise `AppException` subclasses (not generic exceptions)
- **DTOs**: use Pydantic models for request/response
- **Entities**: `@dataclass` with `create()` classmethod factory

## Common Tasks

### Add a Database Migration

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Seed Data

```bash
cd backend
python -m app.infrastructure.seed
```

### Run Linting

```bash
cd backend
ruff check app/
ruff format app/ --check
```

## Troubleshooting

- **`ModuleNotFoundError`**: Run `pip install -r requirements.txt`
- **Migration issues**: Delete `test.db` and re-run `alembic upgrade head`
- **Firebase auth errors**: Check `FIREBASE_CREDENTIALS_PATH` in `.env`
- **Redis connection errors**: Verify `REDIS_URL` and Redis server is running
