#!/bin/bash
# OpenClaw Skill Finder Script
# Searches for skills across ClawHub, GitHub, and local system

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$HOME/.openclaw/skill-search"
CACHE_FILE="$CACHE_DIR/skills-cache.json"
CACHE_TTL=86400  # 24 hours in seconds

# Create cache directory
mkdir -p "$CACHE_DIR"

# Function to print header
print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Function to print section
print_section() {
    echo ""
    echo -e "${YELLOW}▸ $1${NC}"
    echo ""
}

# Function to check if cache is valid
cache_valid() {
    if [ ! -f "$CACHE_FILE" ]; then
        return 1
    fi
    
    local cache_age=$(($(date +%s) - $(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE")))
    if [ $cache_age -gt $CACHE_TTL ]; then
        return 1
    fi
    return 0
}

# Function to search local skills
search_local() {
    print_section "🔍 Searching Local System"
    
    # Check npm global skills
    local npm_skills_dir="${NPM_PREFIX:-$HOME/.npm-global}/lib/node_modules/openclaw/skills"
    if [ -d "$npm_skills_dir" ]; then
        echo -e "${BLUE}NPM skills directory:${NC} $npm_skills_dir"
        find "$npm_skills_dir" -name "SKILL.md" -o -name "*.skill" 2>/dev/null | while read -r skill; do
            local name=$(basename "$(dirname "$skill")")
            echo -e "  ${GREEN}✓${NC} $name"
        done
    fi
    
    # Check workspace skills
    local workspace_dir="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
    if [ -d "$workspace_dir" ]; then
        echo -e "\n${BLUE}Workspace skills:${NC}"
        find "$workspace_dir" -name "*.skill" -o -name "SKILL.md" 2>/dev/null | head -20 | while read -r skill; do
            local name=$(basename "$skill" .skill)
            echo -e "  ${GREEN}✓${NC} $name"
        done
    fi
}

# Function to search GitHub
search_github() {
    local query="$1"
    print_section "🐙 Searching GitHub"
    
    echo -e "${BLUE}Searching for 'openclaw skill $query'...${NC}"
    
    # Use curl to search GitHub API
    local results=$(curl -s "https://api.github.com/search/repositories?q=openclaw+skill+$query&sort=updated&per_page=10" 2>/dev/null || echo '{}')
    
    # Parse and display results
    echo "$results" | python3 -c '
import json, sys
data = json.load(sys.stdin)
items = data.get("items", [])
if not items:
    print("  No GitHub results found")
else:
    for item in items[:5]:
        name = item.get("name", "unknown")
        desc = item.get("description", "No description")[:60]
        stars = item.get("stargazers_count", 0)
        url = item.get("html_url", "")
        print(f"  ⭐ {stars:3d} │ {name:20s} │ {desc}...")
        print(f"      {url}")
        print()
' 2>/dev/null || echo "  (Install python3 for better GitHub parsing)"
}

# Function to fetch from ClawHub (if API available)
search_clawhub() {
    local query="$1"
    print_section "🐾 Searching ClawHub"
    
    echo -e "${BLUE}Manual search URLs:${NC}"
    echo -e "  ${CYAN}https://clawhub.ai/search?q=$query${NC}"
    echo -e "  ${CYAN}https://clawhub.ai/skills?category=$query${NC}"
    echo ""
    echo -e "${YELLOW}Note:${NC} ClawHub requires browser access. Visit the URLs above manually."
}

# Function to search by category
search_by_category() {
    local category="$1"
    print_header "SKILL CATEGORY: ${category^^}"
    
    case "$category" in
        trading|finance|crypto)
            search_local
            search_github "trading"
            search_github "crypto"
            search_clawhub "trading"
            ;;
        agent|agents|team)
            search_local
            search_github "agent"
            search_github "workflow"
            search_clawhub "agents"
            ;;
        data|database|storage)
            search_local
            search_github "database"
            search_github "csv"
            search_clawhub "data"
            ;;
        api|webhook|http)
            search_local
            search_github "api"
            search_github "webhook"
            search_clawhub "api"
            ;;
        *)
            search_local
            search_github "$category"
            search_clawhub "$category"
            ;;
    esac
}

# Function to list all installed skills
list_installed() {
    print_header "INSTALLED SKILLS"
    
    # System skills
    print_section "System Skills (NPM)"
    ls -1 "${NPM_PREFIX:-$HOME/.npm-global}/lib/node_modules/openclaw/skills/" 2>/dev/null | while read -r skill; do
        if [ -d "${NPM_PREFIX:-$HOME/.npm-global}/lib/node_modules/openclaw/skills/$skill" ]; then
            local desc=""
            if [ -f "${NPM_PREFIX:-$HOME/.npm-global}/lib/node_modules/openclaw/skills/$skill/SKILL.md" ]; then
                desc=$(head -5 "${NPM_PREFIX:-$HOME/.npm-global}/lib/node_modules/openclaw/skills/$skill/SKILL.md" | grep -m1 "description:" | cut -d: -f2 | xargs)
            fi
            echo -e "  ${GREEN}●${NC} ${CYAN}$skill${NC} ${desc:+- $desc}"
        fi
    done
    
    # Workspace skills
    local workspace_dir="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
    print_section "Workspace Skills"
    find "$workspace_dir" -name "*.skill" -type d 2>/dev/null | while read -r skill_path; do
        local skill=$(basename "$skill_path" .skill)
        echo -e "  ${GREEN}●${NC} ${CYAN}$skill${NC}"
    done
}

# Function to install a skill (placeholder)
install_skill() {
    local skill_name="$1"
    print_header "INSTALL SKILL: $skill_name"
    
    echo -e "${YELLOW}Installation options:${NC}"
    echo ""
    echo "1. From GitHub:"
    echo "   openclaw skills add github.com/user/$skill_name"
    echo ""
    echo "2. From ClawHub (manual):"
    echo "   Visit https://clawhub.ai/skills/$skill_name"
    echo ""
    echo "3. From local file:"
    echo "   openclaw skills add ./path/to/$skill_name.skill"
    echo ""
}

# Function to show help
show_help() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║            OpenClaw Skill Finder v1.0                        ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
  ./find-skills.sh [command] [options]

COMMANDS:
  search <query>        Search for skills by keyword
  category <name>       Search by category (trading, agents, data, api)
  list                  List all installed skills
  install <name>        Show installation options for a skill
  update                Update skill cache
  help                  Show this help message

EXAMPLES:
  ./find-skills.sh search trading     # Search for trading skills
  ./find-skills.sh category crypto    # Crypto/finance category
  ./find-skills.sh list               # Show installed skills
  ./find-skills.sh install alpaca     # Show install options

CATEGORIES:
  trading, finance, crypto   - Trading bots, market data, exchanges
  agents, team               - Agent coordination, task management
  data, database, storage    - Data processing, databases
  api, webhook, http         - API integrations, webhooks

SOURCES:
  • Local system (NPM + workspace)
  • GitHub repositories
  • ClawHub (manual browser links)

EOF
}

# Main script logic
main() {
    local command="${1:-help}"
    local arg="${2:-}"
    
    case "$command" in
        search)
            if [ -z "$arg" ]; then
                echo -e "${RED}Error: Search query required${NC}"
                echo "Usage: $0 search <query>"
                exit 1
            fi
            print_header "SEARCHING: $arg"
            search_local
            search_github "$arg"
            search_clawhub "$arg"
            ;;
        category|cat)
            if [ -z "$arg" ]; then
                echo -e "${RED}Error: Category required${NC}"
                echo "Usage: $0 category <name>"
                echo "Categories: trading, agents, data, api"
                exit 1
            fi
            search_by_category "$arg"
            ;;
        list|ls)
            list_installed
            ;;
        install|add)
            if [ -z "$arg" ]; then
                echo -e "${RED}Error: Skill name required${NC}"
                echo "Usage: $0 install <skill-name>"
                exit 1
            fi
            install_skill "$arg"
            ;;
        update)
            rm -f "$CACHE_FILE"
            echo -e "${GREEN}✓ Cache cleared${NC}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            show_help
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Run main function
main "$@"
