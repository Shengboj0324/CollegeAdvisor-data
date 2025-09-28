#!/bin/bash

# CollegeAdvisor Production Setup Script
set -e

echo "🚀 CollegeAdvisor Production Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
DOMAIN=${1:-"localhost"}
EMAIL=${2:-"admin@example.com"}
ENVIRONMENT=${3:-"production"}

# Create production directories
create_directories() {
    log_info "Creating production directories..."
    
    mkdir -p {chroma_data,logs,ssl,backups,monitoring}
    mkdir -p logs/{api,chromadb,ollama,nginx}
    mkdir -p monitoring/{prometheus,grafana}
    
    # Set proper permissions
    chmod 755 chroma_data logs ssl backups monitoring
    chmod 644 logs/*
    
    log_success "Directories created"
}

# Generate SSL certificates
generate_ssl() {
    log_info "Generating SSL certificates..."
    
    if [ ! -f ssl/cert.pem ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/key.pem \
            -out ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN}"
        
        log_success "SSL certificates generated"
    else
        log_warning "SSL certificates already exist"
    fi
}

# Setup environment configuration
setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Copy production environment template
    if [ ! -f .env ]; then
        cp .env.production .env
        
        # Replace placeholders
        sed -i.bak "s/yourdomain.com/${DOMAIN}/g" .env
        sed -i.bak "s/your-production-secret-key-change-this/$(openssl rand -hex 32)/g" .env
        sed -i.bak "s/your-jwt-secret-change-this/$(openssl rand -hex 32)/g" .env
        
        rm .env.bak
        log_success "Environment configuration created"
    else
        log_warning "Environment file already exists"
    fi
}

# Setup monitoring configuration
setup_monitoring() {
    log_info "Setting up monitoring configuration..."
    
    # Create Grafana configuration
    cat > monitoring/grafana/datasources.yml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Create Grafana dashboard configuration
    cat > monitoring/grafana/dashboards.yml << EOF
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Monitoring configuration created"
}

# Setup backup scripts
setup_backups() {
    log_info "Setting up backup scripts..."
    
    cat > scripts/backup_data.sh << 'EOF'
#!/bin/bash
# CollegeAdvisor Data Backup Script

BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "${BACKUP_DIR}/${DATE}"

# Backup ChromaDB data
if [ -d "/app/chroma_data" ]; then
    tar -czf "${BACKUP_DIR}/${DATE}/chroma_data.tar.gz" -C /app chroma_data
    echo "ChromaDB data backed up"
fi

# Backup configuration
tar -czf "${BACKUP_DIR}/${DATE}/config.tar.gz" .env docker-compose.yml nginx.conf

# Clean old backups (keep last 7 days)
find "${BACKUP_DIR}" -type d -mtime +7 -exec rm -rf {} +

echo "Backup completed: ${BACKUP_DIR}/${DATE}"
EOF

    chmod +x scripts/backup_data.sh
    
    # Create restore script
    cat > scripts/restore_data.sh << 'EOF'
#!/bin/bash
# CollegeAdvisor Data Restore Script

BACKUP_DATE=${1}
BACKUP_DIR="/app/backups"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la "${BACKUP_DIR}"
    exit 1
fi

if [ ! -d "${BACKUP_DIR}/${BACKUP_DATE}" ]; then
    echo "Backup not found: ${BACKUP_DATE}"
    exit 1
fi

# Stop services
docker-compose down

# Restore ChromaDB data
if [ -f "${BACKUP_DIR}/${BACKUP_DATE}/chroma_data.tar.gz" ]; then
    rm -rf chroma_data
    tar -xzf "${BACKUP_DIR}/${BACKUP_DATE}/chroma_data.tar.gz"
    echo "ChromaDB data restored"
fi

# Restore configuration
tar -xzf "${BACKUP_DIR}/${BACKUP_DATE}/config.tar.gz"

# Restart services
docker-compose up -d

echo "Restore completed from: ${BACKUP_DATE}"
EOF

    chmod +x scripts/restore_data.sh
    
    log_success "Backup scripts created"
}

# Setup log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/collegeadvisor << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose restart nginx
    endscript
}
EOF

    log_success "Log rotation configured"
}

# Setup systemd service (for non-Docker deployments)
setup_systemd() {
    log_info "Setting up systemd service..."
    
    cat > /etc/systemd/system/collegeadvisor.service << EOF
[Unit]
Description=CollegeAdvisor RAG System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/app/collegeadvisor
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable collegeadvisor
    
    log_success "Systemd service configured"
}

# Setup firewall rules
setup_firewall() {
    log_info "Setting up firewall rules..."
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow SSH (be careful!)
    ufw allow 22/tcp
    
    # Allow monitoring ports (restrict to internal network in production)
    ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
    ufw allow from 10.0.0.0/8 to any port 3000  # Grafana
    
    log_success "Firewall rules configured"
}

# Performance tuning
setup_performance_tuning() {
    log_info "Setting up performance tuning..."
    
    # Docker daemon configuration
    cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "default-ulimits": {
        "nofile": {
            "Name": "nofile",
            "Hard": 64000,
            "Soft": 64000
        }
    }
}
EOF

    # System limits
    cat >> /etc/security/limits.conf << EOF
* soft nofile 64000
* hard nofile 64000
* soft nproc 32000
* hard nproc 32000
EOF

    # Kernel parameters
    cat >> /etc/sysctl.conf << EOF
# CollegeAdvisor optimizations
vm.max_map_count=262144
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
EOF

    sysctl -p
    
    log_success "Performance tuning configured"
}

# Main setup function
main() {
    log_info "Starting production setup for domain: ${DOMAIN}"
    
    create_directories
    generate_ssl
    setup_environment
    setup_monitoring
    setup_backups
    setup_log_rotation
    
    # Optional system-level configurations (uncomment if needed)
    # setup_systemd
    # setup_firewall
    # setup_performance_tuning
    
    log_success "Production setup completed!"
    
    echo ""
    log_info "Next Steps:"
    echo "1. Review and customize .env file"
    echo "2. Update SSL certificates for your domain"
    echo "3. Configure monitoring alerts"
    echo "4. Run: ./deploy.sh deploy"
    echo "5. Test all endpoints"
    echo "6. Setup automated backups"
}

# Run main function
main "$@"
