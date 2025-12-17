# clipsmith

**clipsmith** is a social video creation and sharing platform built for scalability and clean architecture.

## 🚀 Tech Stack

- **Backend**: Python (FastAPI), SQLModel (SQLite), JWT, Argon2.
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Zustand.
- **Infrastructure**: Docker, Docker Compose.

## 🏗 Architecture

The project follows **Clean Architecture** and **Domain-Driven Design (DDD)** principles:
- **Domain Layer**: Pure business entities and interfaces.
- **Application Layer**: Use cases and business logic.
- **Infrastructure Layer**: Adapters for DB, Filesystem, Auth.
- **Presentation Layer**: HTTP API (routers).

## 🏃‍♂️ Quick Start

### Using Docker (Recommended)
Deploy the full stack with one command:
```bash
./deploy.sh
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

### Local Development

**Backend**:
```bash
# Setup venv
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Run
uvicorn backend.main:app --reload --port 8001
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## 📝 Features
- **Authentication**: Secure Register/Login (JWT).
- **Video Upload**: Upload processing and metadata storage.
- **Video Feed**: Public stream of user content.
- **Parameters**: User Profiles with video grids.
- **Social**: Likes and Comments.

## 📄 Documentation
See `project_summary.md` (in artifacts) or `walkthrough.md` for detailed development logs.
