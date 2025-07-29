#!/bin/bash
# Vibe Investor Management Script
# Easy commands for controlling your trading system

set -e

COMPOSE_FILE="docker-compose.yml"

show_help() {
    echo "🎯 Vibe Investor Management Commands"
    echo "====================================="
    echo ""
    echo "System Control:"
    echo "  start        Start the trading system"
    echo "  stop         Stop the trading system"
    echo "  restart      Restart the trading system"
    echo "  status       Show system status"
    echo ""
    echo "Monitoring:"
    echo "  logs         Show live logs"
    echo "  dashboard    Open dashboard in browser"
    echo "  health       Check system health"
    echo ""
    echo "Data Management:"
    echo "  backup       Create backup of all data"
    echo "  restore      Restore from backup (interactive)"
    echo "  reset        Reset system (removes all data!)"
    echo ""
    echo "Development:"
    echo "  build        Rebuild containers"
    echo "  update       Update system (pull + rebuild)"
    echo "  shell        Open shell in main container"
    echo ""
    echo "Examples:"
    echo "  ./manage.sh start"
    echo "  ./manage.sh logs"
    echo "  ./manage.sh backup"
    echo ""
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed"
        exit 1
    fi
}

start_system() {
    echo "🚀 Starting Vibe Investor..."
    docker-compose up -d
    echo "✅ System started!"
    echo "📊 Dashboard: http://localhost:8080"
    echo "📝 Logs: ./manage.sh logs"
}

stop_system() {
    echo "🛑 Stopping Vibe Investor..."
    docker-compose down
    echo "✅ System stopped!"
}

restart_system() {
    echo "🔄 Restarting Vibe Investor..."
    docker-compose restart
    echo "✅ System restarted!"
}

show_status() {
    echo "📊 System Status:"
    echo "=================="
    docker-compose ps
    echo ""
    echo "💾 Docker Resources:"
    docker system df
}

show_logs() {
    echo "📝 Live Logs (Ctrl+C to exit):"
    echo "==============================="
    docker-compose logs -f --tail=100
}

open_dashboard() {
    echo "🌐 Opening dashboard..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8080
    elif command -v open &> /dev/null; then
        open http://localhost:8080
    else
        echo "📊 Dashboard available at: http://localhost:8080"
    fi
}

check_health() {
    echo "🏥 System Health Check:"
    echo "======================="
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Containers are running"
    else
        echo "❌ Some containers are not running"
        docker-compose ps
        return 1
    fi
    
    # Check API health
    if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ API is responding"
    else
        echo "❌ API is not responding"
    fi
    
    # Check database connection
    if docker-compose exec -T postgres pg_isready -U trader > /dev/null 2>&1; then
        echo "✅ Database is healthy"
    else
        echo "❌ Database connection issues"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is healthy"
    else
        echo "❌ Redis connection issues"
    fi
    
    echo ""
    echo "📈 Quick Stats:"
    # Add more health checks here when the application is built
    echo "   Check the dashboard for detailed metrics"
}

create_backup() {
    BACKUP_DIR="backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="vibe_investor_backup_${TIMESTAMP}"
    
    echo "💾 Creating backup: ${BACKUP_NAME}"
    
    # Create backup directory
    mkdir -p $BACKUP_DIR
    
    # Database backup
    echo "🗄️  Backing up database..."
    docker-compose exec -T postgres pg_dump -U trader vibe_investor > "${BACKUP_DIR}/${BACKUP_NAME}_database.sql"
    
    # Configuration backup
    echo "⚙️  Backing up configuration..."
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz" .env docker-compose.yml
    
    # Data backup
    echo "📁 Backing up application data..."
    if [ -d "data" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_data.tar.gz" data/
    fi
    
    # Logs backup (last 7 days)
    echo "📝 Backing up recent logs..."
    if [ -d "logs" ]; then
        find logs/ -name "*.log" -mtime -7 -exec tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_logs.tar.gz" {} +
    fi
    
    echo "✅ Backup complete!"
    echo "📦 Backup files:"
    ls -la "${BACKUP_DIR}/${BACKUP_NAME}"*
}

build_system() {
    echo "🔨 Building containers..."
    docker-compose build
    echo "✅ Build complete!"
}

update_system() {
    echo "📥 Updating system..."
    git pull
    docker-compose pull
    docker-compose build
    docker-compose up -d
    echo "✅ Update complete!"
}

open_shell() {
    echo "🐚 Opening shell in main container..."
    docker-compose exec vibe-investor bash
}

reset_system() {
    echo "⚠️  WARNING: This will delete ALL data!"
    echo "This includes:"
    echo "- All trading history"
    echo "- Database contents"
    echo "- Logs and cached data"
    echo ""
    read -p "Are you sure? Type 'DELETE ALL DATA' to confirm: " confirmation
    
    if [ "$confirmation" = "DELETE ALL DATA" ]; then
        echo "🗑️  Stopping system..."
        docker-compose down -v
        
        echo "🧹 Removing data..."
        rm -rf data/ logs/
        docker volume prune -f
        
        echo "✅ System reset complete!"
        echo "🚀 Run './manage.sh start' to start fresh"
    else
        echo "❌ Reset cancelled"
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        check_docker
        start_system
        ;;
    stop)
        check_docker
        stop_system
        ;;
    restart)
        check_docker
        restart_system
        ;;
    status)
        check_docker
        show_status
        ;;
    logs)
        check_docker
        show_logs
        ;;
    dashboard)
        open_dashboard
        ;;
    health)
        check_docker
        check_health
        ;;
    backup)
        check_docker
        create_backup
        ;;
    build)
        check_docker
        build_system
        ;;
    update)
        check_docker
        update_system
        ;;
    shell)
        check_docker
        open_shell
        ;;
    reset)
        check_docker
        reset_system
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 