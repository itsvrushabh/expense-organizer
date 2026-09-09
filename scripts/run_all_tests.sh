#!/usr/bin/env bash
# ==============================================================================
# Master Test Runner & Coverage Aggregator
# Runs Unit Tests, UI Tests, Regression Tests, and Smoke Tests across all components.
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}==============================================================================${NC}"
echo -e "${BOLD}${BLUE}   🧪 EXPENSE ORGANIZER - COMPREHENSIVE TEST SUITE & COVERAGE RUNNER         ${NC}"
echo -e "${BOLD}${BLUE}==============================================================================${NC}"

FAILURES=0

# ------------------------------------------------------------------------------
# 1. Backend Python Tests (Unit, Regression, Smoke)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${YELLOW}[1/5] Running Core Backend Test Suite & Coverage...${NC}"
if pytest backend/tests --cov=backend --cov-report=term-missing; then
    echo -e "${GREEN}✔ Backend Tests Passed!${NC}"
else
    echo -e "${RED}✖ Backend Tests Failed!${NC}"
    FAILURES=$((FAILURES + 1))
fi

# ------------------------------------------------------------------------------
# 2. AI Backend Tests (Unit, Regression, Smoke)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${YELLOW}[2/5] Running AI Backend Test Suite & Coverage...${NC}"
if pytest aibackend/tests --cov=aibackend/app --cov-report=term-missing; then
    echo -e "${GREEN}✔ AI Backend Tests Passed!${NC}"
else
    echo -e "${RED}✖ AI Backend Tests Failed!${NC}"
    FAILURES=$((FAILURES + 1))
fi

# ------------------------------------------------------------------------------
# 3. AI Model Server Tests (Unit, Regression, Smoke)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${YELLOW}[3/5] Running AI Model Server Test Suite...${NC}"
if pytest aimodel/tests; then
    echo -e "${GREEN}✔ AI Model Server Tests Passed!${NC}"
else
    echo -e "${RED}✖ AI Model Server Tests Failed!${NC}"
    FAILURES=$((FAILURES + 1))
fi

# ------------------------------------------------------------------------------
# 4. Web UI Tests (Unit, UI, Smoke via Bun)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${YELLOW}[4/5] Running Web UI Test Suite & Coverage (Bun)...${NC}"
if (cd frontend && bun test --coverage); then
    echo -e "${GREEN}✔ Web UI Tests Passed!${NC}"
else
    echo -e "${RED}✖ Web UI Tests Failed!${NC}"
    FAILURES=$((FAILURES + 1))
fi

# ------------------------------------------------------------------------------
# 5. Mobile App Tests (Unit, Widget UI, Regression, Smoke via Flutter)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${YELLOW}[5/5] Running Mobile App Test Suite & Coverage (Flutter)...${NC}"
if (cd mobile && flutter test --coverage); then
    echo -e "${GREEN}✔ Mobile App Tests Passed!${NC}"
else
    echo -e "${RED}✖ Mobile App Tests Failed!${NC}"
    FAILURES=$((FAILURES + 1))
fi

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${BLUE}==============================================================================${NC}"
if [ $FAILURES -eq 0 ]; then
    echo -e "${BOLD}${GREEN}🎉 ALL TEST SUITES PASSED WITH FULL COVERAGE!${NC}"
    echo -e "${BOLD}${BLUE}==============================================================================${NC}"
    exit 0
else
    echo -e "${BOLD}${RED}⚠️ $FAILURES TEST SUITE(S) FAILED. Please review the logs above.${NC}"
    echo -e "${BOLD}${BLUE}==============================================================================${NC}"
    exit 1
fi
