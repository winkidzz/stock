#!/bin/bash

# Stock Screener - Docker Setup with Host Ollama
# This script starts the application stack using Docker while connecting to host Ollama

echo "🐳 Stock Screener - Docker Setup (Host Ollama)"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Check if Ollama is running on host
check_host_ollama() {
    print_status "Checking Ollama on host machine..."
    
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama is not installed on host machine!"
        exit 1
    fi
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        print_error "Ollama is not running on host machine!"
        echo "Please start Ollama with: ollama serve"
        exit 1
    fi
    
    print_status "Ollama is running on host ✓"
}

# Check available models
check_models() {
    print_status "Checking available models on host..."
    
    # Get list of available models
    MODELS=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}')
    
    if [ -z "$MODELS" ]; then
        print_error "No models found on host Ollama!"
        echo "Please install at least one model:"
        echo "  ollama pull llama3:8b"
        echo "  ollama pull gemma3:27b"
        exit 1
    fi
    
    print_status "Available models:"
    echo "$MODELS" | while read -r model; do
        echo "  ✓ $model"
    done
}

# Setup environment for Docker
setup_docker_env() {
    print_status "Setting up Docker environment..."
    
    # Create .env from template if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.local ]; then
            cp .env.local .env
            print_status "Created .env from .env.local"
        else
            print_error ".env.local not found!"
            exit 1
        fi
    fi
    
    # Update Ollama URL for Docker containers
    sed -i.bak 's|OLLAMA_BASE_URL=.*|OLLAMA_BASE_URL=http://host.docker.internal:11434|' .env
    print_status "Updated .env for Docker containers"
}

# Test Docker connectivity to host Ollama
test_docker_ollama() {
    print_status "Testing Docker connectivity to host Ollama..."
    
    # Start a temporary container to test connectivity
    if docker run --rm curlimages/curl:latest -s http://host.docker.internal:11434/api/tags > /dev/null 2>&1; then
        print_status "Docker can connect to host Ollama ✓"
    else
        print_warning "Docker connectivity test failed, but continuing..."
        print_status "This might work once all services are running"
    fi
}

# Start the application stack
start_application_stack() {
    print_status "Starting application stack with Docker Compose..."
    
    # Check if docker-compose.yml exists
    if [ ! -f docker-compose.yml ]; then
        print_error "docker-compose.yml not found!"
        exit 1
    fi
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose down
    
    # Build and start the services
    print_status "Building and starting services..."
    docker-compose up -d --build
    
    # Wait for services to start
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check service health
    print_status "Checking service health..."
    
    # Check PostgreSQL
    if docker-compose exec postgres pg_isready -U postgres &> /dev/null; then
        print_status "PostgreSQL is ready ✓"
    else
        print_warning "PostgreSQL not ready yet"
    fi
    
    # Check Redis
    if docker-compose exec redis redis-cli ping &> /dev/null; then
        print_status "Redis is ready ✓"
    else
        print_warning "Redis not ready yet"
    fi
    
    # Check application
    if curl -s http://localhost:8000/health &> /dev/null; then
        print_status "Application is ready ✓"
    else
        print_warning "Application not ready yet, may need more time"
    fi
}

# Show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo
    print_status "Application URLs:"
    echo "  🌐 API Documentation: http://localhost:8000/docs"
    echo "  ❤️  Health Check: http://localhost:8000/health"
    echo "  📊 Database: localhost:5432 (postgres/postgres)"
    echo "  🔄 Redis: localhost:6379"
    echo "  🤖 Ollama: localhost:11434 (host machine)"
    
    echo
    print_status "Useful Commands:"
    echo "  📋 View logs: docker-compose logs -f"
    echo "  🔄 Restart: docker-compose restart"
    echo "  🛑 Stop: docker-compose down"
    echo "  🗑️  Clean: docker-compose down -v"
}

# Main execution
main() {
    echo
    print_status "Starting Docker setup process..."
    
    # Run checks
    check_host_ollama
    check_models
    setup_docker_env
    test_docker_ollama
    start_application_stack
    
    echo
    print_status "Setup complete! 🎉"
    echo
    
    show_status
    
    echo
    print_status "To test the integration:"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://localhost:8000/stocks"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        print_status "Stopping all services..."
        docker-compose down
        exit 0
        ;;
    "logs")
        print_status "Showing logs..."
        docker-compose logs -f
        exit 0
        ;;
    "status")
        show_status
        exit 0
        ;;
    "clean")
        print_status "Cleaning up all containers and volumes..."
        docker-compose down -v
        docker system prune -f
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo "Commands:"
        echo "  (none)  - Start the application stack"
        echo "  stop    - Stop all services"
        echo "  logs    - Show service logs"
        echo "  status  - Show service status"
        echo "  clean   - Clean up containers and volumes"
        echo "  help    - Show this help"
        exit 0
        ;;
esac

# Run main function
main "$@" 