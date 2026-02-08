# Todo AI Chatbot - Cloud Deployment

A full-stack AI-powered todo application with task management, conversation interface, and Kubernetes deployment.

## Project Structure

```
.
├── backend/              # FastAPI backend service
├── frontend/             # Next.js frontend application
├── kubernetes/           # Kubernetes deployment manifests
├── docker/               # Docker configurations
├── helm-charts/          # Helm deployment charts
├── specs/                # Feature specifications and plans
├── history/              # PHRs and ADRs
├── .specify/             # SpecKit templates and constitution
├── src/                  # Core source code
├── tests/                # Test suites
├── scripts/              # Utility scripts
├── db/                   # Database migrations and schemas
├── docs/                 # Project documentation
└── misc/                 # Archived/old files
    ├── demo-files/       # Demo scripts and examples
    ├── test-files/       # Old test files
    ├── deployment-docs/  # Historical deployment docs
    ├── old-configs/      # Legacy configuration files
    ├── backup-files/     # Backup directories
    └── temp-files/       # Temporary and cache files
```

## Key Directories

### Active Development
- **backend/** - Python FastAPI server with AI integration
- **frontend/** - Next.js App Router application
- **kubernetes/** - K8s manifests for cloud deployment
- **specs/** - SDD artifacts (spec.md, plan.md, tasks.md)

### Infrastructure
- **docker/** - Container configurations
- **helm-charts/** - Kubernetes Helm charts
- **scripts/** - Deployment and utility scripts

### Documentation & History
- **history/** - Prompt History Records (PHRs) and ADRs
- **.specify/** - SpecKit Plus templates and constitution
- **docs/** - Current documentation

### Archived
- **misc/** - Old files, demos, and temporary artifacts

## Quick Start

1. **Setup Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Run Backend**
   ```bash
   cd backend
   uvicorn app:app --reload
   ```

3. **Run Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Deploy to Kubernetes**
   ```bash
   cd kubernetes
   kubectl apply -f todo-ai-chatbot-final-deployment.yaml
   ```

## Technologies

- **Backend:** Python 3.13+, FastAPI, SQLModel
- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Database:** Neon Serverless PostgreSQL
- **Infrastructure:** Docker, Kubernetes, Helm
- **AI:** OpenAI GPT integration

## Features

- Task management with CRUD operations
- AI-powered chatbot for natural language task creation
- Recursive subtasks and categories
- Real-time updates
- Kubernetes-ready cloud deployment
- Mobile-first responsive design

## Documentation

See the `docs/` directory for detailed documentation. Historical documentation has been archived in `misc/deployment-docs/`.

## Development Workflow

This project follows Spec-Driven Development (SDD). See `.specify/memory/constitution.md` for coding standards and `CLAUDE.md` for agent guidelines.
