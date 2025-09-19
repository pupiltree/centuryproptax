#!/bin/bash

# Clear Redis Sessions Script
# Quick commands for clearing conversation sessions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Krsnaa Diagnostics - Session Manager${NC}"
echo "----------------------------------------"

# Default to Python script
if [ $# -eq 0 ]; then
    # No arguments - show menu
    echo "Quick Actions:"
    echo "  1) List all sessions"
    echo "  2) Clear all sessions"
    echo "  3) Clear specific user sessions"
    echo "  4) Show session details"
    echo "  5) Exit"
    echo
    read -p "Select action (1-5): " choice
    
    case $choice in
        1)
            python "$SCRIPT_DIR/clear-redis.py" --list
            ;;
        2)
            echo -e "${YELLOW}⚠️  Warning: This will clear ALL sessions${NC}"
            read -p "Are you sure? (y/N): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                python "$SCRIPT_DIR/clear-redis.py" --all --yes
            else
                echo "Cancelled"
            fi
            ;;
        3)
            read -p "Enter user ID to clear: " user_id
            if [ -n "$user_id" ]; then
                python "$SCRIPT_DIR/clear-redis.py" --user "$user_id"
            else
                echo "No user ID provided"
            fi
            ;;
        4)
            read -p "Enter thread ID to inspect: " thread_id
            if [ -n "$thread_id" ]; then
                python "$SCRIPT_DIR/clear-redis.py" --details "$thread_id"
            else
                echo "No thread ID provided"
            fi
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    # Pass arguments to Python script
    python "$SCRIPT_DIR/clear-redis.py" "$@"
fi