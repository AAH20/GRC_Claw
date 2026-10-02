# Interview Scheduler

AI-powered interview scheduling service with calendar integration, timezone handling, and conflict resolution.

## Features

- **5 AI Agents**: Calendar Sync, Timezone Resolution, Conflict Detection, Availability Optimization, Reminders
- **Calendar Integrations**: Google Calendar, Outlook Calendar
- **Timezone Handling**: Automatic timezone conversion and resolution
- **Conflict Resolution**: Detect and resolve scheduling conflicts
- **REST API**: 10+ endpoints for full interview lifecycle management
- **Production Ready**: Docker, Kubernetes, CI/CD included

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run locally
uvicorn interview_scheduler.main:create_app --factory --reload

# Run with Docker
docker-compose up --build

# Run tests
pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/interviews` | List interviews |
| POST | `/api/v1/interviews` | Create interview |
| GET | `/api/v1/interviews/{id}` | Get interview |
| PUT | `/api/v1/interviews/{id}` | Update interview |
| DELETE | `/api/v1/interviews/{id}` | Delete interview |
| GET | `/api/v1/schedules` | List schedules |
| POST | `/api/v1/schedules` | Create schedule |
| GET | `/api/v1/timeslots` | List available time slots |
| POST | `/api/v1/timeslots/find` | Find optimal time slots |
| GET | `/api/v1/conflicts` | List conflicts |
| POST | `/api/v1/conflicts/detect` | Detect conflicts |
| GET | `/api/v1/reminders` | List reminders |
| POST | `/api/v1/reminders` | Create reminder |
| POST | `/api/v1/agents/schedule` | Run full scheduling pipeline |

## Architecture

```
src/interview_scheduler/
├── agents/          # LangChain DeepAgents
│   ├── calendar_sync.py
│   ├── timezone_resolver.py
│   ├── conflict_detector.py
│   ├── availability_optimizer.py
│   └── reminder.py
├── api/             # FastAPI routes
│   └── routes/
├── config/          # Settings
├── integrations/    # Calendar providers
├── models/          # Pydantic schemas
├── services/        # Business logic
└── main.py          # App factory
```

## License

MIT
