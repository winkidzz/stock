#!/bin/bash

# Stock Screener - Local LLM Setup Script
# This script helps set up and run the stock screener with local LLM support

echo "🚀 Stock Screener - Local LLM Setup"
echo "=================================="

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

# Check if Ollama is installed
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama is not installed!"
        echo "Please install Ollama from: https://ollama.ai/"
        echo "Then run: ollama serve"
        exit 1
    fi
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        print_error "Ollama is not running!"
        echo "Please start Ollama with: ollama serve"
        exit 1
    fi
    
    print_status "Ollama is running ✓"
}

# Check if required models are available
check_models() {
    print_status "Checking available models..."
    
    # Get list of available models
    MODELS=$(ollama list | tail -n +2 | awk '{print $1}')
    
    # Check for recommended models
    RECOMMENDED_MODELS=("llama3:8b" "gemma3:27b" "mistral:latest")
    AVAILABLE_MODELS=()
    
    for model in "${RECOMMENDED_MODELS[@]}"; do
        if echo "$MODELS" | grep -q "$model"; then
            AVAILABLE_MODELS+=("$model")
            print_status "Found model: $model ✓"
        else
            print_warning "Model $model not found"
        fi
    done
    
    if [ ${#AVAILABLE_MODELS[@]} -eq 0 ]; then
        print_error "No recommended models found!"
        echo "Please install at least one model:"
        echo "  ollama pull llama3:8b"
        echo "  ollama pull gemma3:27b"
        echo "  ollama pull mistral:latest"
        exit 1
    fi
    
    # Use the first available model as default
    DEFAULT_MODEL=${AVAILABLE_MODELS[0]}
    print_status "Using default model: $DEFAULT_MODEL"
}

# Set up environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Copy environment file
    if [ ! -f .env ]; then
        if [ -f .env.local ]; then
            cp .env.local .env
            print_status "Created .env from .env.local"
        else
            print_error ".env.local not found!"
            exit 1
        fi
    fi
    
    # Update model configuration in .env
    if [ -n "$DEFAULT_MODEL" ]; then
        sed -i.bak "s/LLM_MODEL=.*/LLM_MODEL=$DEFAULT_MODEL/" .env
        sed -i.bak "s/LLM_MODEL_FAST=.*/LLM_MODEL_FAST=$DEFAULT_MODEL/" .env
        print_status "Updated .env with available model"
    fi
}

# Check Python dependencies
check_dependencies() {
    print_status "Checking Python dependencies..."
    
    if [ ! -f requirements.txt ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    print_status "Dependencies installed ✓"
}

# Test model connectivity
test_model() {
    print_status "Testing model connectivity..."
    
    # Simple test query
    RESPONSE=$(ollama run "$DEFAULT_MODEL" "Hello, respond with just 'OK'" 2>/dev/null)
    
    if [[ "$RESPONSE" == *"OK"* ]]; then
        print_status "Model test successful ✓"
    else
        print_warning "Model test failed, but continuing..."
    fi
}

# Start the application
start_application() {
    print_status "Starting Stock Screener application..."
    
    # Check if database is needed
    print_status "Checking database connection..."
    if ! python -c "
import sys
sys.path.insert(0, 'src')
try:
    from database.connection import check_database_health
    exit(0 if check_database_health() else 1)
except Exception as e:
    print(f'Database check failed: {e}')
    exit(1)
" 2>/dev/null; then
        print_warning "Database not available. Consider starting PostgreSQL or using Docker."
        print_status "You can start the database with: docker-compose up postgres -d"
        print_status "Or run without database for testing: python test_local_llm.py"
        
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_status "Database connection successful ✓"
    fi
    
    # Start the application
    print_status "Starting FastAPI server..."
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Health Check: http://localhost:8000/health"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python run_local.py
}

# Main execution
main() {
    echo
    print_status "Starting setup process..."
    
    # Run checks
    check_ollama
    check_models
    setup_environment
    check_dependencies
    test_model
    
    echo
    print_status "Setup complete! 🎉"
    echo
    print_status "Available models in your system:"
    echo "$MODELS"
    echo
    print_status "Configuration:"
    echo "  Primary Model: $DEFAULT_MODEL"
    echo "  Fast Model: $DEFAULT_MODEL"
    echo "  Ollama URL: http://localhost:11434"
    echo
    
    # Ask if user wants to start the application
    read -p "Start the application now? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_status "Setup complete. Run './start_with_local_llm.sh' to start the application."
        exit 0
    fi
    
    start_application
}

# Run main function
main "$@" 