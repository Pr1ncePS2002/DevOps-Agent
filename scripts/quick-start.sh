#!/usr/bin/env bash
# ============================================================
# AI DevOps Commander — Quick Start
# Usage: ./scripts/quick-start.sh
# ============================================================
set -e

CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

banner() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${CYAN}║     AI DevOps Commander — Quick Start    ║${RESET}"
  echo -e "${CYAN}╚══════════════════════════════════════════╝${RESET}"
  echo ""
}

check_prereqs() {
  echo -e "${CYAN}[1/4] Checking prerequisites...${RESET}"

  if ! command -v docker &>/dev/null; then
    echo -e "${RED}✗ Docker not found. Install from https://docs.docker.com/get-docker/${RESET}"
    exit 1
  fi
  echo -e "${GREEN}✓ Docker$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1 | sed 's/^/ /')${RESET}"

  # Support both docker-compose and docker compose
  if command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
  elif docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  else
    echo -e "${RED}✗ Docker Compose not found. Update Docker Desktop or install docker-compose.${RESET}"
    exit 1
  fi
  echo -e "${GREEN}✓ Docker Compose available${RESET}"
}

setup_env() {
  echo -e "${CYAN}[2/4] Setting up environment...${RESET}"

  if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠  .env created from .env.example${RESET}"
    echo -e "${YELLOW}   Add your API keys before deploying real projects:${RESET}"
    echo -e "${YELLOW}   • GEMINI_API_KEY (recommended — free at aistudio.google.com)${RESET}"
    echo -e "${YELLOW}   • or OPENAI_API_KEY${RESET}"
    echo ""
  else
    echo -e "${GREEN}✓ .env already exists${RESET}"
  fi

  # Warn if no LLM key is set
  if grep -qE "^GEMINI_API_KEY=$" .env && grep -qE "^OPENAI_API_KEY=$" .env; then
    echo -e "${YELLOW}⚠  No LLM API key detected. AI features will use the deterministic fallback.${RESET}"
    echo -e "${YELLOW}   Set GEMINI_API_KEY in .env for full AI experience.${RESET}"
    echo ""
  fi
}

build_and_start() {
  echo -e "${CYAN}[3/4] Building and starting services...${RESET}"
  echo -e "      (First build may take 3-5 minutes)"
  echo ""
  $COMPOSE_CMD up --build -d
}

wait_for_health() {
  echo ""
  echo -e "${CYAN}[4/4] Waiting for services to be ready...${RESET}"

  local retries=30
  local count=0
  while [ $count -lt $retries ]; do
    if curl -sf http://localhost:3001/health >/dev/null 2>&1; then
      echo -e "${GREEN}✓ Backend is healthy${RESET}"
      break
    fi
    count=$((count + 1))
    echo -ne "  Attempt $count/$retries...\r"
    sleep 3
  done

  if [ $count -eq $retries ]; then
    echo -e "${RED}✗ Backend did not start in time. Check logs: $COMPOSE_CMD logs backend${RESET}"
    exit 1
  fi
}

print_success() {
  echo ""
  echo -e "${GREEN}╔══════════════════════════════════════════╗${RESET}"
  echo -e "${GREEN}║          Stack is up and running!        ║${RESET}"
  echo -e "${GREEN}╚══════════════════════════════════════════╝${RESET}"
  echo ""
  echo -e "  ${CYAN}Dashboard:${RESET}  http://localhost:3000"
  echo -e "  ${CYAN}API:${RESET}        http://localhost:3001"
  echo -e "  ${CYAN}API Docs:${RESET}   http://localhost:3001/docs"
  echo ""
  echo -e "  To stop: ${YELLOW}$COMPOSE_CMD down${RESET}"
  echo -e "  Logs:    ${YELLOW}$COMPOSE_CMD logs -f${RESET}"
  echo ""
}

# ── Main ──────────────────────────────────────────────────────────────────────

# Must be run from repo root
cd "$(dirname "$0")/.."

banner
check_prereqs
setup_env
build_and_start
wait_for_health
print_success
