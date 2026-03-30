#!/usr/bin/env python3
"""Setup and manage email monitor webhooks."""

import argparse
import sys
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from email_monitor import WebhookManager


def cmd_setup(webhook_url: str):
    """Set up a new webhook."""
    try:
        manager = WebhookManager()
        webhook_id = manager.setup_webhook(webhook_url)
        print(f"✅ Webhook created successfully!")
        print(f"   Webhook ID: {webhook_id}")
        print(f"   URL: {webhook_url}")
        print(f"   Listening for: message.received events")
        
    except Exception as e:
        print(f"❌ Failed to setup webhook: {e}")
        sys.exit(1)


def cmd_list():
    """List existing webhooks."""
    try:
        manager = WebhookManager()
        webhooks = manager.list_webhooks()
        
        if not webhooks:
            print("No webhooks found")
            return
            
        print(f"Found {len(webhooks)} webhook(s):")
        for wh in webhooks:
            status = "✅ enabled" if wh["enabled"] else "❌ disabled"
            print(f"  {wh['id']}: {wh['url']} ({status})")
            
    except Exception as e:
        print(f"❌ Failed to list webhooks: {e}")
        sys.exit(1)


def cmd_delete(webhook_id: str):
    """Delete a webhook."""
    try:
        manager = WebhookManager()
        success = manager.delete_webhook(webhook_id)
        
        if success:
            print(f"✅ Webhook {webhook_id} deleted successfully")
        else:
            print(f"❌ Failed to delete webhook {webhook_id}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to delete webhook: {e}")
        sys.exit(1)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Email Monitor Webhook Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup new webhook")
    setup_parser.add_argument("url", help="Webhook URL (e.g., https://your-domain.com/webhook)")
    
    # List command
    subparsers.add_parser("list", help="List existing webhooks")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete webhook")
    delete_parser.add_argument("id", help="Webhook ID to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "setup":
        cmd_setup(args.url)
    elif args.command == "list":
        cmd_list()
    elif args.command == "delete":
        cmd_delete(args.id)


if __name__ == "__main__":
    main()