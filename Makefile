.PHONY: help install start stop test clean migrate

help:
	@echo "Available commands:"
	@echo "  make install    - Install all dependencies"
	@echo "  make start      - Start all services with Docker Compose"
	@echo "  make stop       - Stop all services"
	@echo "  make test       - Run all tests"
	@echo "  make test-backend - Run backend tests only"
	@echo "  make test-frontend - Run frontend tests only"
	@echo "  make migrate    - Run database migrations"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make logs       - Show logs from all services"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Dependencies installed!"

start:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started! Backend: http://localhost:8000 | Frontend: http://localhost:3000"

stop:
	@echo "Stopping all services..."
	docker-compose down
	@echo "Services stopped!"

test: test-backend test-frontend
	@echo "All tests completed!"

test-backend:
	@echo "Running backend tests..."
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test -- --run

migrate:
	@echo "Running database migrations..."
	docker-compose exec backend alembic upgrade head
	@echo "Migrations completed!"

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration name: " name; \
	docker-compose exec backend alembic revision --autogenerate -m "$$name"

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "Cleanup completed!"

logs:
	docker-compose logs -f

build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "Build completed!"

dev-backend:
	@echo "Starting backend in development mode..."
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting frontend in development mode..."
	cd frontend && npm run dev
