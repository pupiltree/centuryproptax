#!/usr/bin/env python3
"""
Clear Redis data for a specific user in Krsnaa Diagnostics.
Works with the actual key patterns used by the system.
"""

import redis
import sys
import argparse

def clear_user_data(user_id, dry_run=False):
    """Clear all Redis data for a specific user."""
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print(f"✅ Connected to Redis successfully")
        
        # Find all keys containing the user ID
        user_keys = r.keys(f"*{user_id}*")
        
        if not user_keys:
            print(f"ℹ️  No keys found for user: {user_id}")
            return 0
        
        print(f"📊 Found {len(user_keys)} keys for user {user_id}:")
        
        # Group keys by type for better display
        key_types = {}
        for key in user_keys:
            if key.startswith("conversation_state:"):
                key_types.setdefault("Conversation State", []).append(key)
            elif key.startswith("snapshot:"):
                key_types.setdefault("Snapshots", []).append(key)
            elif key.startswith("snapshot_index:"):
                key_types.setdefault("Snapshot Index", []).append(key)
            else:
                key_types.setdefault("Other", []).append(key)
        
        for key_type, keys in key_types.items():
            print(f"  📁 {key_type}: {len(keys)} keys")
            for key in keys[:3]:  # Show first 3 keys of each type
                print(f"     • {key}")
            if len(keys) > 3:
                print(f"     ... and {len(keys) - 3} more")
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would delete {len(user_keys)} keys")
            return len(user_keys)
        
        # Delete all keys
        if len(user_keys) > 0:
            deleted_count = r.delete(*user_keys)
            print(f"\n✅ Successfully deleted {deleted_count} keys for user {user_id}")
            return deleted_count
        
        return 0
        
    except redis.ConnectionError:
        print("❌ Could not connect to Redis. Is it running?")
        return -1
    except Exception as e:
        print(f"❌ Error: {e}")
        return -1

def main():
    parser = argparse.ArgumentParser(description="Clear Redis data for a specific user")
    parser.add_argument("user_id", help="User ID to clear (e.g., Instagram ID)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    
    args = parser.parse_args()
    
    print(f"🔄 Clearing Redis data for user: {args.user_id}")
    print("-" * 60)
    
    deleted = clear_user_data(args.user_id, args.dry_run)
    
    if deleted > 0:
        if args.dry_run:
            print(f"\n💡 Run without --dry-run to actually delete the keys")
        else:
            print(f"\n🎉 User session cleared! They can start a fresh conversation.")
    elif deleted == 0:
        print(f"\n💭 No session data found for user {args.user_id}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()