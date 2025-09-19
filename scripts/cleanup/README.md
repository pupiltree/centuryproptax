# Database Cleanup Scripts

This directory contains scripts to clear user data and reset the system.

## 🗑️ Available Scripts

### 1. `clear-all-data.py` - Complete Wipe
**Clears EVERYTHING**: All user data, conversation history, orders, tickets, and sessions.

```bash
# ⚠️ DANGER: This deletes ALL user data
python scripts/cleanup/clear-all-data.py --confirm
```

**What it clears:**
- ❌ All SQLite tables (customers, bookings, tickets, messages)  
- ❌ All Redis keys (sessions, orders, conversation state)
- ❌ All conversation checkpoints
- ❌ All ticket data and agent sessions

**Use when:** Starting completely fresh or testing from scratch

---

### 2. `clear-sessions-only.py` - Soft Reset
**Clears only sessions**: Conversation state cleared, but order/ticket history preserved.

```bash
# Safe: Only clears active sessions
python scripts/cleanup/clear-sessions-only.py
```

**What it clears:**
- ❌ Conversation state and LangGraph checkpoints
- ❌ Active user sessions and message batches  
- ❌ Cached order data in Redis
- ✅ **Preserves**: Customer profiles, booking history, support tickets

**Use when:** Users need to restart conversations but keep their history

---

### 3. Individual Scripts (Already existing)
- `clear-user-redis.py` - Clear specific user's Redis data
- `clear-all-sessions.py` - Clear all LangGraph sessions

---

## 🚀 Quick Reference

| Need | Script | Data Loss | Safe? |
|------|--------|-----------|--------|
| Fresh start | `cleanup/clear-all-data.py --confirm` | **ALL DATA** | ⚠️ Use carefully |
| Reset conversations | `cleanup/clear-sessions-only.py` | Sessions only | ✅ Safe |
| Clear one user | `cleanup/clear-user-redis.py` | One user's session | ✅ Safe |

---

## 🔍 What Each Database Stores

### Redis (Temporary/Session Data)
```
session_*           - LangGraph conversation checkpoints
user_batch_*        - Message batching queues  
order:*             - Cached order data (24h TTL)
ticket_status:*     - Active ticket status
agent_response:*    - Pending agent messages
```

### SQLite (Persistent Data)
```
customers           - Customer profiles and contact info
test_bookings       - Completed booking records
support_tickets     - Customer service tickets
ticket_messages     - Chat history with agents
agent_sessions      - Agent activity tracking
```

---

## 🛡️ Safety Notes

1. **Always backup first** if running on production
2. **Test scripts** on development before production use  
3. **`clear-all-data.py` requires `--confirm`** flag for safety
4. **`clear-sessions-only.py`** is generally safe to run anytime
5. **Check logs** for any errors during cleanup

---

## 📊 Usage Examples

### 🎯 Easy Interactive Mode (Recommended)
```bash
# Interactive cleanup tool with menu
./scripts/cleanup/run-cleanup.sh
```

### 🔧 Direct Script Commands
```bash
# Complete fresh start (DESTRUCTIVE) - requires virtual environment
source venv/bin/activate
python scripts/cleanup/clear-all-data.py --confirm

# Just reset conversations (SAFE)  
source venv/bin/activate
python scripts/cleanup/clear-sessions-only.py

# Clear specific user's session
python scripts/cleanup/clear-user-redis.py user_123456

# Clear all sessions but keep data
python scripts/cleanup/clear-all-sessions.py
```

The scripts include detailed logging to show exactly what's being cleared!