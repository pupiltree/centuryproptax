#!/usr/bin/env python3
"""
Clear ALL user sessions from Redis for Krsnaa Diagnostics.
"""

import redis
import argparse

def clear_all_sessions(confirm=False, dry_run=False):
    """Clear all conversation-related keys from Redis."""
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Connected to Redis successfully")
        
        # Key patterns to clear
        patterns = [
            "conversation_state:*",
            "snapshot:*", 
            "snapshot_index:*"
        ]
        
        all_keys = set()
        for pattern in patterns:
            keys = r.keys(pattern)
            all_keys.update(keys)
        
        if not all_keys:
            print("ℹ️  No session keys found to delete")
            return 0
        
        keys_list = list(all_keys)
        print(f"📊 Found {len(keys_list)} session keys to delete")
        
        # Group by pattern for display
        for pattern in patterns:
            matching = [k for k in keys_list if k.startswith(pattern.replace('*', ''))]
            if matching:
                print(f"  📁 {pattern}: {len(matching)} keys")
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would delete {len(keys_list)} session keys")
            print("💡 Run without --dry-run to actually delete")
            return len(keys_list)
        
        if not confirm:
            print(f"\n⚠️  WARNING: This will delete ALL {len(keys_list)} session keys!")
            print("   This will clear conversation history for ALL users.")
            response = input("   Type 'DELETE ALL' to confirm: ")
            if response != 'DELETE ALL':
                print("❌ Operation cancelled")
                return -1
        
        # Delete all keys
        if keys_list:
            deleted_count = r.delete(*keys_list)
            print(f"\n✅ Successfully deleted {deleted_count} session keys")
            print("🎉 All user sessions cleared! Everyone starts fresh.")
            return deleted_count
        
        return 0
        
    except redis.ConnectionError:
        print("❌ Could not connect to Redis. Is it running?")
        return -1
    except Exception as e:
        print(f"❌ Error: {e}")
        return -1

def main():
    parser = argparse.ArgumentParser(description="Clear ALL user sessions from Redis")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    
    args = parser.parse_args()
    
    print("🔄 Clearing ALL user sessions from Redis")
    print("=" * 50)
    
    deleted = clear_all_sessions(confirm=args.yes, dry_run=args.dry_run)
    
    if deleted < 0:
        exit(1)
    elif deleted == 0 and not args.dry_run:
        print("💭 No sessions found to clear")

if __name__ == "__main__":
    main()