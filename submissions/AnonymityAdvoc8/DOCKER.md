# 🐳 Docker Deployment Guide

Complete guide for containerized deployment of the Banking Client.

## 🚀 Quick Start with Docker

### Option 1: Docker Compose (Recommended)

```bash
# Start both server and client
docker-compose up -d

# Run a transfer
docker-compose run --rm banking-client transfer --from ACC1000 --to ACC1001 --amount 100

# Stop all services
docker-compose down
```

### Option 2: Docker Only

```bash
# Build the image
docker build -t banking-client .

# Run CLI commands
docker run --rm banking-client transfer --from ACC1000 --to ACC1001 --amount 100

# Run with custom environment
docker run --rm \
  -e API_BASE_URL=http://host.docker.internal:8123 \
  -e ENABLE_AUTHENTICATION=true \
  banking-client transfer --from ACC1000 --to ACC1001 --amount 50
```

---

## 📋 Docker Compose Commands

### Start Services
```bash
# Start in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up banking-server
```

### Run Banking Operations
```bash
# Transfer money
docker-compose run --rm banking-client transfer --from ACC1000 --to ACC1001 --amount 100

# Validate account
docker-compose run --rm banking-client validate --account ACC1000

# Check balance
docker-compose run --rm banking-client balance --account ACC1000

# List all accounts
docker-compose run --rm banking-client list

# Run demo script
docker-compose run --rm banking-client python example_usage.py

# Run with verbose logging
docker-compose run --rm banking-client --verbose transfer --from ACC1000 --to ACC1001 --amount 50
```

### With Authentication
```bash
# Enable JWT auth via environment variable
ENABLE_AUTHENTICATION=true docker-compose run --rm banking-client transfer --from ACC1000 --to ACC1001 --amount 100

# Custom credentials
ENABLE_AUTHENTICATION=true \
  AUTH_USERNAME=myuser \
  AUTH_PASSWORD=mypass \
  docker-compose run --rm banking-client list
```

### Monitoring & Logs
```bash
# View logs
docker-compose logs -f

# View server logs only
docker-compose logs -f banking-server

# View client logs only
docker-compose logs -f banking-client

# Check health
docker-compose run --rm banking-client python health_check.py --verbose
```

### Cleanup
```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove everything including volumes
docker-compose down -v

# Rebuild services
docker-compose build

# Rebuild and restart
docker-compose up -d --build
```

---

## 🔧 Docker Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://banking-server:8123` | Banking API URL |
| `ENABLE_AUTHENTICATION` | `false` | Enable JWT authentication |
| `AUTH_USERNAME` | `admin` | Authentication username |
| `AUTH_PASSWORD` | `password123` | Authentication password |
| `LOG_LEVEL` | `INFO` | Logging level |

### Health Checks

**Banking Server:**
- Endpoint: `GET /accounts/validate/ACC1000`
- Interval: 10s
- Timeout: 3s
- Retries: 3

**Banking Client:**
- Command: `python health_check.py`
- Interval: 30s
- Timeout: 3s
- Retries: 3

---

## 🏗️ Multi-Stage Build

The Dockerfile uses multi-stage build for optimization:

**Stage 1: Builder**
- Compiles dependencies
- Installs packages

**Stage 2: Runtime**
- Minimal Python 3.12 slim image
- Copies only necessary files
- Runs as non-root user
- ~200MB final image size

---

## 🔒 Security Features

1. **Non-root user** - Runs as `bankinguser` (UID 1000)
2. **Minimal base image** - `python:3.12-slim`
3. **No dev dependencies** - Production only
4. **Environment-based secrets** - No hardcoded credentials
5. **Health checks** - Automatic restart on failure

---

## 📊 Image Information

```bash
# View image size
docker images banking-client

# Inspect image
docker inspect banking-client:latest

# View image layers
docker history banking-client:latest
```

---

## 🚀 Production Deployment

### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml banking

# Scale client
docker service scale banking_banking-client=3

# Remove stack
docker stack rm banking
```

### Kubernetes (example deployment)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: banking-client
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: banking-client
        image: banking-client:latest
        env:
        - name: API_BASE_URL
          value: "http://banking-server:8123"
        - name: ENABLE_AUTHENTICATION
          valueFrom:
            secretKeyRef:
              name: banking-secrets
              key: enable-auth
```

---

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs banking-client

# Check health
docker-compose ps

# Restart
docker-compose restart banking-client
```

### Can't connect to server
```bash
# Verify server is healthy
docker-compose ps banking-server

# Check server health
curl http://localhost:8123/accounts/validate/ACC1000

# Check network
docker network inspect banking-network
```

### Permission issues
```bash
# Rebuild without cache
docker-compose build --no-cache

# Check user
docker-compose run --rm banking-client whoami
```

---

## 📝 Best Practices

1. **Use docker-compose** for local development
2. **Set environment variables** in `.env` file
3. **Use health checks** for production
4. **Monitor logs** regularly
5. **Update images** regularly
6. **Use volume mounts** for development:
   ```bash
   docker-compose run --rm -v $(pwd):/app banking-client list
   ```

---

**Built with ❤️ for containerized deployments**

