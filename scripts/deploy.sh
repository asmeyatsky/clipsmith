#!/bin/bash

# Clipsmith Deployment Script
# This script automates the deployment of clipsmith to production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"
PROJECT_NAME="clipsmith"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_status "Dependencies check passed ✓"
}

# Environment setup
setup_environment() {
    print_status "Setting up $ENVIRONMENT environment..."
    
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ ! -f ".env.production" ]; then
            print_error "Production environment file .env.production not found!"
            exit 1
        fi
        
        # Copy production environment file
        cp .env.production .env
        print_status "Production environment configured ✓"
    else
        print_status "Development environment configured ✓"
    fi
}

# Database setup
setup_database() {
    print_status "Setting up database..."
    
    # Create database init script if it doesn't exist
    if [ ! -f "database/init.sql" ]; then
        mkdir -p database
        cat > database/init.sql << EOF
-- Create database and user if they don't exist
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'clipsmith') THEN
        CREATE USER clipsmith WITH PASSWORD 'clipsmith_password';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_database WHERE datname = 'clipsmith') THEN
        CREATE DATABASE clipsmith OWNER clipsmith;
    END IF;
    
    GRANT ALL PRIVILEGES ON DATABASE clipsmith TO clipsmith;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO clipsmith;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO clipsmith;
END $$;
EOF
        print_status "Database init script created ✓"
    fi
    
    print_status "Database setup completed ✓"
}

# SSL certificate setup (only for production)
setup_ssl() {
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Setting up SSL certificates..."
        
        # Create SSL directory structure
        mkdir -p nginx/ssl
        
        if [ ! -f "nginx/ssl/cert.pem" ]; then
            print_warning "SSL certificates not found. Using self-signed certificates for development."
            
            # Generate self-signed certificates (for development only)
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout nginx/ssl/key.pem \
                -out nginx/ssl/cert.pem \
                -subj "/C=US/ST=California/L=San Francisco/O=Clipsmith/CN=clipsmith.com"
            
            print_status "Self-signed SSL certificates generated ✓"
        else
            print_status "SSL certificates found ✓"
        fi
    fi
}

# Nginx configuration setup
setup_nginx() {
    print_status "Setting up Nginx configuration..."
    
    mkdir -p nginx
    
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name _;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        
        client_max_body_size 100M;
        
        # Backend API routes
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static file serving
        location /uploads/ {
            alias /var/www/static/uploads/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    print_status "Nginx configuration created ✓"
}

# Monitoring setup
setup_monitoring() {
    print_status "Setting up monitoring stack..."
    
    mkdir -p monitoring/grafana/{dashboards,datasources}
    
    # Grafana datasources configuration
    cat > monitoring/grafana/datasources/clipsmith.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
    
    # Grafana dashboard configuration
    cat > monitoring/grafana/dashboards/clipsmith.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
    
    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "clipsmith_rules.yml"

scrape_configs:
  - job_name: 'clipsmith-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
    
  - job_name: 'clipsmith-nginx'
    static_configs:
      - targets: ['nginx:9113']
    metrics_path: /metrics
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
    
    print_status "Monitoring configuration created ✓"
}

# Backup setup
setup_backups() {
    print_status "Setting up backup system..."
    
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
# Clipsmith Backup Script

BACKUP_DIR="/backup"
DATE=\$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Starting database backup..."
docker exec clipsmith-postgres pg_dump -U clipsmith clipsmith | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# File backup
echo "Starting file backup..."
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz uploads/

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x scripts/backup.sh
    mkdir -p scripts
    
    print_status "Backup system configured ✓"
}

# Main deployment function
deploy() {
    print_status "Starting Clipsmith deployment to $ENVIRONMENT..."
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose -f $COMPOSE_FILE down --remove-orphans || true
    
    # Build and start services
    print_status "Building and starting services..."
    docker-compose -f $COMPOSE_FILE up -d --build
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    
    # Wait for database
    timeout 60 bash -c 'until docker exec clipsmith-postgres pg_isready -U clipsmith; do sleep 2; done'
    
    # Wait for backend
    timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
    
    # Wait for frontend
    timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 2; done'
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec backend python -c "
from backend.infrastructure.repositories.database import create_db_and_tables
create_db_and_tables()
print('Database migrations completed')
"
    
    print_status "Deployment completed successfully! ✓"
    
    # Show status
    echo ""
    print_status "=== DEPLOYMENT STATUS ==="
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    print_status "=== SERVICE URLs ==="
    echo "Frontend: https://localhost"
    echo "Backend API: https://localhost/api"
    echo "Grafana: https://localhost:3001 (admin/admin)"
    echo "Prometheus: https://localhost:9090"
}

# Health check function
health_check() {
    print_status "Running health checks..."
    
    # Check if all containers are running
    containers=$(docker-compose -f $COMPOSE_FILE ps -q)
    if [ -z "$containers" ]; then
        print_error "No containers are running!"
        return 1
    fi
    
    # Check service health
    services=("postgres" "redis" "backend" "frontend" "nginx")
    
    for service in "${services[@]}"; do
        if docker ps --filter "name=clipsmith-$service" --filter "status=running" | grep -q .; then
            print_status "$service is running ✓"
        else
            print_error "$service is not running ✗"
        fi
    done
    
    # API health check
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_status "Backend API is healthy ✓"
    else
        print_error "Backend API is not responding ✗"
    fi
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    docker-compose -f $COMPOSE_FILE down --volumes --remove-orphans || true
    docker system prune -f
    print_status "Cleanup completed ✓"
}

# Logs function
show_logs() {
    service=$1
    if [ -z "$service" ]; then
        docker-compose -f $COMPOSE_FILE logs -f
    else
        docker-compose -f $COMPOSE_FILE logs -f $service
    fi
}

# Update function
update() {
    print_status "Updating deployment..."
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Redeploy with zero downtime
    if [ "$ENVIRONMENT" = "production" ]; then
        # Rolling update strategy would go here
        docker-compose -f $COMPOSE_FILE up -d --no-deps
    else
        docker-compose -f $COMPOSE_FILE up -d --build
    fi
    
    print_status "Update completed ✓"
}

# Main script logic
case "$1" in
    deploy)
        check_dependencies
        setup_environment
        setup_database
        setup_ssl
        setup_nginx
        setup_monitoring
        setup_backups
        deploy
        ;;
    health)
        health_check
        ;;
    logs)
        show_logs "$2"
        ;;
    cleanup)
        cleanup
        ;;
    update)
        update
        ;;
    *)
        echo "Usage: $0 {deploy|health|logs|cleanup|update} [service_name]"
        echo ""
        echo "Commands:"
        echo "  deploy    - Deploy the application"
        echo "  health    - Check service health"
        echo "  logs      - Show service logs (optional: service_name)"
        echo "  cleanup   - Stop and remove all containers"
        echo "  update    - Update the deployment"
        echo ""
        echo "Examples:"
        echo "  $0 deploy"
        echo "  $0 health"
        echo "  $0 logs backend"
        echo "  $0 cleanup"
        exit 1
        ;;
esac