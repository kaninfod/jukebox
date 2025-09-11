#!/bin/bash

# Jukebox Test Runner Script
# Run different types of tests for the jukebox application

set -e

echo "🧪 Jukebox Test Suite"
echo "===================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run tests with proper error handling
run_tests() {
    local test_type="$1"
    local test_files="$2"
    local description="$3"
    
    echo -e "\n${BLUE}🔍 Running $description${NC}"
    echo "----------------------------------------"
    
    if python -m pytest $test_files -v; then
        echo -e "${GREEN}✅ $description passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed!${NC}"
        return 1
    fi
}

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing test dependencies...${NC}"
    pip install -r requirements-test.txt
fi

# Initialize test results
TOTAL_TESTS=0
PASSED_TESTS=0

# Run Unit Tests
if run_tests "unit" "tests/test_services.py" "Unit Tests (Individual Services)"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))

# Run Integration Tests
if run_tests "integration" "tests/test_system_integration.py" "Integration Tests (System Components)"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))

# Run User Workflow Tests
if run_tests "workflows" "tests/test_user_workflows.py" "User Workflow Tests (End-to-End Patterns)"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))

# Run all tests with coverage
echo -e "\n${BLUE}📊 Running Full Test Suite with Coverage${NC}"
echo "----------------------------------------"
if python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing; then
    echo -e "${GREEN}✅ Coverage report generated in htmlcov/index.html${NC}"
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))

# Final Results
echo -e "\n${BLUE}📋 Test Summary${NC}"
echo "================"
echo -e "Total test suites: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Your dependency injection is working perfectly!${NC}"
    exit 0
else
    echo -e "\n${RED}🔧 Some tests failed. Check the output above for details.${NC}"
    exit 1
fi
