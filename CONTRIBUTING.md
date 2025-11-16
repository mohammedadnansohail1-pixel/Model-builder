# Contributing to UniversalTune

Thank you for your interest in contributing to UniversalTune!

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (for local development)
- Redis 7+ (for local development)

### Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/universaltune.git
cd universaltune
```

2. Copy the environment file:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start with Docker Compose (recommended):
```bash
make start
```

Or for local development:

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Testing

Run all tests:
```bash
make test
```

Run backend tests only:
```bash
make test-backend
```

Run frontend tests only:
```bash
make test-frontend
```

## Code Style

### Backend (Python)

- Follow PEP 8
- Use Black for formatting: `black backend/`
- Use isort for imports: `isort backend/`
- Use mypy for type checking: `mypy backend/`

### Frontend (TypeScript/React)

- Follow ESLint rules
- Use Prettier for formatting: `npm run format`
- Use TypeScript strict mode

## Commit Messages

Follow conventional commits:
- `feat: Add new feature`
- `fix: Fix bug`
- `docs: Update documentation`
- `test: Add tests`
- `refactor: Refactor code`
- `chore: Update dependencies`

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `make test`
4. Commit your changes with conventional commit messages
5. Push to your fork: `git push origin feature/your-feature`
6. Open a Pull Request

## Questions?

Open an issue or reach out to the maintainers!
