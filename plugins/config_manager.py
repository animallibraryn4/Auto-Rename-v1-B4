# config_manager.py
import datetime
from helper.database import n4bots

class DynamicConfig:
    def __init__(self):
        self.cache = {}
        self.last_update = {}
    
    async def get_settings(self):
        """Get bot settings with caching"""
        cache_key = "bot_settings"
        if cache_key in self.cache:
            # Cache for 30 seconds
            if (datetime.datetime.now() - self.last_update[cache_key]).seconds < 30:
                return self.cache[cache_key]
        
        settings = await n4bots.get_bot_settings()
        if settings:
            self.cache[cache_key] = settings
            self.last_update[cache_key] = datetime.datetime.now()
        return settings
    
    async def is_premium_user(self, user_id):
        """Check if user is premium"""
        # Check cache first
        cache_key = f"premium_{user_id}"
        if cache_key in self.cache:
            if (datetime.datetime.now() - self.last_update[cache_key]).seconds < 60:
                return self.cache[cache_key]
        
        premium_user = await n4bots.get_premium_user(user_id)
        is_premium = premium_user is not None
        self.cache[cache_key] = is_premium
        self.last_update[cache_key] = datetime.datetime.now()
        return is_premium
    
    async def get_verify_config(self):
        """Get verification configuration"""
        settings = await self.get_settings()
        if not settings:
            return {
                "verify_enabled": True,
                "verify_photo": "https://images8.alphacoders.com/138/1384114.png",
                "verify_tutorial": "https://t.me/N4_Society/55",
                "shortlink_site": "gplinks.com",
                "shortlink_api": "596f423cdf22b174e43d0b48a36a8274759ec2a3",
                "verify_expire": 30000
            }
        return settings

# Global instance
config_manager = DynamicConfig()
