# License Server

A self-hosted software license management system for controlling user access to software tools with device-based limitations.

## Features

- **License Key Generation** - Cryptographically secure keys in `XXXX-XXXX-XXXX-XXXX` format
- **Device-Based Activation** - Hardware fingerprint binding (CPU, disk, motherboard, MAC)
- **One License Per Device** - Prevent unauthorized sharing
- **Admin Dashboard** - React-based UI for license management
- **REST API** - Full API with OpenAPI/Swagger documentation
- **Python SDK** - Easy integration for your tools

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.11+ for local development

### 1. Clone and Configure

```bash
git clone <repository-url>
cd licenseToolServer

# Copy environment file
cp backend/.env.example backend/.env
```

### 2. Edit Environment Variables

```bash
# backend/.env
DJANGO_SECRET_KEY=your-secure-random-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=license_server
DB_USER=root
DB_PASSWORD=your-secure-password
```

### 3. Start with Docker

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. Initialize

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create admin user (default: admin/admin123)
docker-compose exec backend python manage.py setup_admin
```

### 5. Access

| Service | URL |
|---------|-----|
| Admin Dashboard | http://localhost |
| API Documentation | http://localhost/api/docs/ |
| Django Admin | http://localhost/admin/ |

## Project Structure

```
licenseToolServer/
├── backend/           # Django REST API
│   ├── apps/licenses/ # License management app
│   └── config/        # Django settings
├── frontend/          # React admin dashboard
├── sdk/               # Python client SDK
├── nginx/             # Nginx configuration
├── docs/              # Documentation
└── docker-compose.yml # Docker configuration
```

## SDK Usage

Install the SDK in your tool:

```bash
cd sdk
pip install -e .
```

Integrate license checking:

```python
from license_client import LicenseClient

client = LicenseClient(
    server_url="https://your-license-server.com",
    cache_file="~/.myapp/license.json"
)

# Activate on first run
client.activate("XXXX-XXXX-XXXX-XXXX")

# Check license on subsequent runs
if not client.is_valid():
    print("Valid license required")
    exit(1)

# Your application code here
```

## API Endpoints

### Public Endpoints (No Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/activate/` | Activate a license on a device |
| POST | `/api/v1/deactivate/` | Deactivate a license |
| POST | `/api/v1/validate/` | Validate a license |
| GET | `/api/v1/health/` | Health check |

### Admin Endpoints (JWT Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/licenses/` | List all licenses |
| POST | `/api/v1/admin/licenses/` | Generate new license |
| GET | `/api/v1/admin/licenses/{id}/` | Get license details |
| DELETE | `/api/v1/admin/licenses/{id}/revoke/` | Revoke a license |
| GET | `/api/v1/admin/devices/` | List all devices |

### Authentication

```bash
# Get JWT token
curl -X POST http://localhost/api/v1/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token for admin endpoints
curl http://localhost/api/v1/admin/licenses/ \
  -H "Authorization: Bearer <access_token>"
```

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r ../requirements.txt

python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
# Backend tests
cd backend
pytest

# SDK tests
cd sdk
pytest
```

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment instructions
- [API Documentation](http://localhost/api/docs/) - Interactive Swagger UI
- [SDK Documentation](sdk/README.md) - Client SDK usage

## Tech Stack

- **Backend:** Django 5.x, Django REST Framework, JWT Authentication
- **Frontend:** React 18, Vite, Tailwind CSS
- **Database:** MySQL 8.x
- **Cache:** Redis
- **Server:** Nginx, Gunicorn
- **Container:** Docker, Docker Compose

## License

MIT License
