# UniversalTune Deployment Guide

This guide covers deploying UniversalTune to production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Production Configuration](#production-configuration)
- [Docker Deployment](#docker-deployment)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Database Setup](#database-setup)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Backup & Recovery](#backup--recovery)
- [Security Hardening](#security-hardening)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- 4 CPU cores
- 16 GB RAM
- 100 GB storage
- Ubuntu 20.04+ or similar Linux distribution

**Recommended:**
- 8+ CPU cores
- 32+ GB RAM
- 500+ GB SSD storage
- NVIDIA GPU (for training workloads)

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- OpenSSL (for certificate generation)
- Git

---

## Production Configuration

### 1. Environment Variables

Copy the production environment template:

```bash
cp .env.production.example .env.production
```

**Critical variables to configure:**

```bash
# Generate secure keys
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 32)
REDIS_PASSWORD=$(openssl rand -hex 32)
MINIO_ROOT_PASSWORD=$(openssl rand -hex 32)

# Update database credentials
POSTGRES_USER=universaltune
POSTGRES_DB=universaltune

# Update MinIO credentials
MINIO_ROOT_USER=admin
MINIO_BUCKET=universaltune

# Configure CORS for your domain
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Configure frontend URL
VITE_API_URL=https://api.yourdomain.com

# Add HuggingFace token (optional but recommended)
HUGGINGFACE_TOKEN=hf_xxxxx

# Add Sentry DSN for error tracking (optional)
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
```

### 2. Security Configuration

**backend/app/core/config.py**

Ensure production settings are enabled:

```python
ENVIRONMENT=production
```

This enables:
- HTTPS enforcement
- Secure cookie settings
- Production CORS policies
- Enhanced rate limiting

---

## Docker Deployment

### 1. Build and Start Services

```bash
# Pull latest code
git pull origin main

# Build and start production containers
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service health
docker-compose -f docker-compose.prod.yml ps
```

### 2. Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 3. Create Initial Admin User

```bash
docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.create_admin_user
```

### 4. Verify Services

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:80

# Check MinIO
curl http://localhost:9000/minio/health/live
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

**1. Install Certbot:**

```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**2. Generate Certificates:**

```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

**3. Copy Certificates:**

```bash
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
```

**4. Auto-Renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### Option 2: Self-Signed Certificates (Development/Testing)

```bash
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

### Option 3: Cloud Provider SSL

If using AWS, GCP, or Azure, use their managed SSL services (ALB, Cloud Load Balancer, Application Gateway).

---

## Database Setup

### 1. PostgreSQL Production Configuration

**Create backup directory:**

```bash
mkdir -p backups
chmod 700 backups
```

**Optimize PostgreSQL settings** (add to docker-compose.prod.yml):

```yaml
postgres:
  environment:
    - POSTGRES_MAX_CONNECTIONS=200
    - POSTGRES_SHARED_BUFFERS=4GB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=12GB
    - POSTGRES_WORK_MEM=16MB
```

### 2. Connection Pooling

The application uses SQLAlchemy connection pooling:

```python
# backend/app/core/config.py
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### 3. Database Backups

**Automated daily backups:**

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/universaltune_${DATE}.sql"

docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U universaltune universaltune > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete
```

**Add to crontab:**

```bash
0 2 * * * /path/to/backup.sh
```

**Restore from backup:**

```bash
gunzip -c backups/universaltune_20240116.sql.gz | \
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U universaltune universaltune
```

---

## Scaling

### 1. Horizontal Scaling with Docker Swarm

**Initialize swarm:**

```bash
docker swarm init
```

**Deploy stack:**

```bash
docker stack deploy -c docker-compose.prod.yml universaltune
```

**Scale services:**

```bash
# Scale backend workers
docker service scale universaltune_backend=3

# Scale Celery workers
docker service scale universaltune_celery-worker=5
```

### 2. Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests:

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/minio.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/celery.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n universaltune
```

### 3. Load Balancing

**Nginx upstream configuration:**

```nginx
upstream backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}
```

---

## Monitoring

### 1. Application Monitoring

**Sentry (Error Tracking):**

```bash
# Set in .env.production
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
```

**Prometheus Metrics:**

Install and configure Prometheus:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'universaltune-backend'
    static_configs:
      - targets: ['backend:8000']
```

### 2. Infrastructure Monitoring

**Docker Stats:**

```bash
docker stats
```

**Resource Monitoring:**

```bash
# Install monitoring tools
docker-compose -f docker-compose.monitoring.yml up -d
```

This starts:
- Prometheus (metrics)
- Grafana (dashboards)
- cAdvisor (container metrics)
- Node Exporter (system metrics)

Access Grafana at `http://localhost:3001`

### 3. Logging

**Centralized logging with ELK Stack:**

```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
```

**View logs:**

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

---

## Backup & Recovery

### 1. Database Backups

**Automated backup script** (see Database Setup section)

**Manual backup:**

```bash
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U universaltune universaltune > backup.sql
```

### 2. File Storage Backups

**MinIO backup:**

```bash
# Using MinIO client
mc alias set myminio http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc mirror myminio/universaltune /backups/minio/
```

### 3. Disaster Recovery

**Full system backup:**

```bash
#!/bin/bash
# full_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/full_${DATE}"

mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U universaltune universaltune > $BACKUP_DIR/database.sql

# Backup MinIO data
docker cp universaltune-minio:/data $BACKUP_DIR/minio

# Backup environment and configs
cp .env.production $BACKUP_DIR/
cp docker-compose.prod.yml $BACKUP_DIR/
cp -r nginx/ $BACKUP_DIR/

# Compress
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

**Recovery:**

```bash
# Extract backup
tar -xzf backups/full_20240116.tar.gz

# Restore database
cat full_20240116/database.sql | \
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U universaltune universaltune

# Restore MinIO
docker cp full_20240116/minio universaltune-minio:/data

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other incoming
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable firewall
sudo ufw enable
```

### 2. Application Security

**Rate Limiting:**

Configured in `nginx/nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
```

**Security Headers:**

Already configured in Nginx:
- Strict-Transport-Security
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

**Input Validation:**

All inputs validated through Pydantic schemas.

### 3. Container Security

**Run as non-root user:**

Already configured in production Dockerfiles.

**Scan for vulnerabilities:**

```bash
docker scan universaltune-backend
docker scan universaltune-frontend
```

### 4. Secrets Management

**Use Docker secrets:**

```bash
echo "your-secret" | docker secret create jwt_secret -
```

**Or use external secrets management:**
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

---

## Troubleshooting

### Common Issues

**1. Services won't start:**

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check memory
free -m
```

**2. Database connection errors:**

```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml exec postgres psql -U universaltune -c '\l'

# Check connection from backend
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.database import engine; print(engine)"
```

**3. High memory usage:**

```bash
# Check container stats
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Reduce worker count if needed
```

**4. SSL certificate errors:**

```bash
# Verify certificates
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Check Nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Performance Tuning

**1. PostgreSQL:**

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Vacuum database
VACUUM ANALYZE;
```

**2. Redis:**

```bash
# Check memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO memory

# Clear cache if needed
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHDB
```

**3. Application:**

```bash
# Monitor request latency
docker-compose -f docker-compose.prod.yml exec backend python -m app.scripts.analyze_performance
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Check service health
- Review error logs
- Monitor disk space

**Weekly:**
- Review security logs
- Check backup integrity
- Update dependencies (security patches)

**Monthly:**
- Performance optimization
- Database maintenance (VACUUM, REINDEX)
- Review and rotate logs

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Verify health
docker-compose -f docker-compose.prod.yml ps
```

---

## Support

For deployment issues:
- GitHub Issues: https://github.com/yourusername/universaltune/issues
- Documentation: https://docs.universaltune.com
- Email: support@universaltune.com
