# 🗑️ Database Cleanup Scripts

All data cleanup scripts have been moved to the `cleanup/` directory.

## 📂 Available Cleanup Scripts

See **[cleanup/README.md](cleanup/README.md)** for detailed documentation.

### Quick Commands:

```bash
# Complete database wipe (⚠️ DESTRUCTIVE)
python scripts/cleanup/clear-all-data.py --confirm

# Reset conversations only (✅ SAFE)
python scripts/cleanup/clear-sessions-only.py

# Clear specific user
python scripts/cleanup/clear-user-redis.py <user_id>

# Clear all sessions
python scripts/cleanup/clear-all-sessions.py
```

## 📁 Directory Structure

```
scripts/
├── cleanup/                    # 🗑️ All cleanup scripts here
│   ├── README.md              # Detailed documentation
│   ├── clear-all-data.py      # Nuclear option - deletes everything
│   ├── clear-sessions-only.py # Safe reset - keeps history
│   ├── clear-user-redis.py    # Clear one user's data
│   └── clear-all-sessions.py  # Clear conversation state
├── test-*.py                  # Integration tests
└── validate-workflow.py       # Workflow validation
```

For detailed usage instructions and safety information, see **[cleanup/README.md](cleanup/README.md)**.