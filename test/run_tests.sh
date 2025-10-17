#!/bin/bash
# PostgreSQL MCP Server Test Runner Script

set -e

echo "=== PostgreSQL MCP Server Test Runner ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Function to run unit tests
run_unit_tests() {
    print_info "Running unit tests..."
    python -m pytest test/unit/ -v --tb=short --cov=src --cov-report=term-missing
}

# Function to run integration tests
run_integration_tests() {
    print_info "Running integration tests..."
    RUN_INTEGRATION_TESTS=1 python -m pytest test/integration/ -v --tb=short -m integration
}

# Function to run all tests with Docker
run_docker_tests() {
    print_info "Starting Docker test environment..."
    cd test/docker
    
    # Build and start services
    docker-compose -f docker-compose.test.yml up --build -d
    
    # Wait for PostgreSQL to be ready
    print_info "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Run tests
    print_info "Running tests in Docker container..."
    docker-compose -f docker-compose.test.yml run --rm test-runner
    
    # Stop services
    print_info "Stopping Docker services..."
    docker-compose -f docker-compose.test.yml down
    
    cd ../..
}

# Function to run specific test type
run_test_type() {
    case $1 in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "docker")
            run_docker_tests
            ;;
        "all")
            run_unit_tests
            run_integration_tests
            ;;
        *)
            print_error "Unknown test type: $1"
            print_info "Available types: unit, integration, docker, all"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    local test_type=${1:-"all"}
    
    print_info "Test type: $test_type"
    
    case $test_type in
        "docker")
            check_docker
            run_docker_tests
            ;;
        "all"|"unit"|"integration")
            if [ "$test_type" = "all" ] || [ "$test_type" = "integration" ]; then
                check_docker
            fi
            run_test_type "$test_type"
            ;;
    esac
    
    print_success "Test execution completed!"
}

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Available test types:"
    echo "  unit        - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo "  docker      - Run all tests in Docker environment"
    echo "  all         - Run all tests (default)"
    echo ""
    echo "Examples:"
    echo "  $0 unit        # Run only unit tests"
    echo "  $0 integration # Run only integration tests"
    echo "  $0 docker      # Run tests in Docker"
    echo "  $0             # Run all tests"
    exit 0
fi

# Run main function
main "$@"
