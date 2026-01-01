# License Server - Deployment Guide

This guide covers deploying the License Server in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Deployment](#manual-deployment)
- [Production Configuration](#production-configuration)
- [Database Setup](#database-setup)
- [Nginx Configuration](#nginx-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ (for manual deployment)
- Node.js 18+ (for frontend build)
- MySQL 8.x or MariaDB 10.x
- Redis 6.x+
- Nginx (for reverse proxy)

## Quick Start with Docker

The fastest way to deploy is using Docker Compose:

### 1. Clone and Configure

```bash
git clone <repository-url>
cd licenseToolServer

# Copy and edit environment file
cp backend/.env.example backend/.env
```

### 2. Edit Environment Variables

```bash
# backend/.env
DJANGO_SECRET_KEY=your-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=license_server
DB_USER=license_user
DB_PASSWORD=secure-password-here
DB_HOST=db
DB_PORT=3306

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### 3. Build and Start

```bash
docker-compose up -d --build
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create admin user
docker-compose exec backend python manage.py setup_admin
```

### 5. Access the Application

- **Admin Dashboard:** https://yourdomain.com
- **API Docs (Swagger):** https://yourdomain.com/api/docs/
- **API Docs (ReDoc):** https://yourdomain.com/api/redoc/

## Manual Deployment

For environments without Docker:

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r ../requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create admin user
python manage.py setup_admin
```

### Frontend Build

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

The built files will be in `frontend/dist/` - serve them with Nginx.

### Run with Gunicorn

```bash
cd backend

gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 30
```

### Run Celery Worker

```bash
cd backend

celery -A config worker -l info
```

## Production Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | **Required.** Random 50+ char string | `abc123...` |
| `DEBUG` | Must be `False` in production | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed domains | `example.com,api.example.com` |
| `DB_NAME` | Database name | `license_server` |
| `DB_USER` | Database username | `license_user` |
| `DB_PASSWORD` | Database password | `secure-password` |
| `DB_HOST` | Database host | `localhost` or `db` |
| `DB_PORT` | Database port | `3306` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |

### Generate Secret Key

```python
# Run in Python shell
import secrets
print(secrets.token_urlsafe(50))
```

## Database Setup

### MySQL Configuration

```sql
CREATE DATABASE license_server CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'license_user'@'%' IDENTIFIED BY 'secure-password';
GRANT ALL PRIVILEGES ON license_server.* TO 'license_user'@'%';
FLUSH PRIVILEGES;
```

### MariaDB Configuration

Same as MySQL above.

## Nginx Configuration

### Basic Configuration

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend (React app)
    location / {
        root /var/www/license-server/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin panel
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static/ {
        alias /var/www/license-server/backend/staticfiles/;
    }
}
```

## SSL/TLS Setup

### Using Let's Encrypt

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

## Monitoring & Logging

### Application Logs

```bash
# Docker logs
docker-compose logs -f backend

# Gunicorn logs
tail -f /var/log/license-server/gunicorn.log
```

### Health Check Endpoint

Add to your monitoring:

```
GET /api/v1/validate/
```

Returns 400 for invalid request (server is up).

### Recommended Monitoring Tools

- **Prometheus + Grafana** - Metrics collection
- **Sentry** - Error tracking
- **ELK Stack** - Log aggregation

## Backup & Recovery

### Database Backup

```bash
# MySQL dump
mysqldump -u license_user -p license_server > backup_$(date +%Y%m%d).sql

# Docker backup
docker-compose exec db mysqldump -u root -p license_server > backup.sql
```

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/license-server"
DATE=$(date +%Y%m%d_%H%M%S)

mysqldump -u license_user -p$DB_PASSWORD license_server | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

Add to cron:
```
0 2 * * * /path/to/backup.sh
```

### Recovery

```bash
# Restore database
mysql -u license_user -p license_server < backup.sql

# Docker restore
docker-compose exec -T db mysql -u root -p license_server < backup.sql
```

## Troubleshooting

### Common Issues

#### 1. "No such table" errors

```bash
# Run migrations
docker-compose exec backend python manage.py migrate
```

#### 2. Static files not loading

```bash
# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

#### 3. Permission denied errors

```bash
# Fix permissions
chown -R www-data:www-data /var/www/license-server
```

#### 4. Redis connection refused

```bash
# Check Redis is running
docker-compose ps redis
redis-cli ping
```

#### 5. CORS errors

Add your frontend domain to `ALLOWED_HOSTS` in `.env`.

### Debug Mode

For debugging production issues (temporary only):

```bash
# Enable debug temporarily
docker-compose exec backend python manage.py shell
>>> from django.conf import settings
>>> print(settings.DEBUG)
```

Never enable `DEBUG=True` in production for extended periods.

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY` (50+ characters)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database password is strong and unique
- [ ] Redis password configured (if exposed)
- [ ] Firewall rules: only expose ports 80, 443
- [ ] Regular security updates applied
- [ ] Database backups configured
- [ ] Log monitoring enabled

## Support

For issues and questions:
- Check the [API Documentation](/api/docs/)
- Review application logs
- Open an issue on GitHub
