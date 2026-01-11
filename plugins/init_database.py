# init_database.py
from helper.database import n4bots

async def initialize_database():
    """Initialize database with default settings"""
    print("Initializing database...")
    
    # Check if bot_settings collection exists
    collections = await n4bots.n4bots.list_collection_names()
    
    if "bot_settings" not in collections:
        print("Creating bot_settings collection...")
        default_settings = {
            "_id": "global",
            "verify_enabled": True,
            "verify_photo": "https://images8.alphacoders.com/138/1384114.png",
            "verify_tutorial": "https://t.me/N4_Society/55",
            "shortlink_site": "gplinks.com",
            "shortlink_api": "596f423cdf22b174e43d0b48a36a8274759ec2a3",
            "verify_expire": 30000,
            "force_sub_channels": ["animelibraryn4"],
            "log_channel": -1002263636517,
            "dump_channel": -1001896877147,
            "start_pic": "https://images8.alphacoders.com/138/1384114.png",
            "admin_users": [5380609667],
            "webhook_enabled": True
        }
        await n4bots.n4bots.bot_settings.insert_one(default_settings)
        print("Default settings created.")
    
    if "premium_users" not in collections:
        print("Creating premium_users collection...")
        # Create with sample index
        await n4bots.n4bots.premium_users.create_index("user_id", unique=True)
        await n4bots.n4bots.premium_users.create_index("expires_at")
        print("Premium users collection created.")
    
    print("Database initialization complete.")

# Run this on bot startup
