import logging
import datetime
from helper.database import n4bots

logger = logging.getLogger(__name__)

async def check_ban_status_simple(user_id):
    """Simple ban check without requiring message object"""
    try:
        # Check if user exists in database
        if await n4bots.is_user_exist(user_id):
            # Get user data to check ban status
            user_data = await n4bots.col.find_one({"_id": int(user_id)})
            
            if user_data:
                ban_status = user_data.get("ban_status", {})
                is_banned = ban_status.get("is_banned", False)
                
                if is_banned:
                    # Check if ban has expired (for temporary bans)
                    ban_duration = ban_status.get("ban_duration", 0)
                    
                    if ban_duration > 0:
                        # Check if ban has expired
                        banned_on_str = ban_status.get("banned_on")
                        try:
                            banned_on = datetime.date.fromisoformat(banned_on_str)
                            today = datetime.date.today()
                            days_banned = (today - banned_on).days
                            
                            if days_banned >= ban_duration:
                                # Ban expired, unban the user
                                await n4bots.col.update_one(
                                    {"_id": int(user_id)},
                                    {"$set": {
                                        "ban_status": {
                                            "is_banned": False,
                                            "ban_duration": 0,
                                            "banned_on": datetime.date.max.isoformat(),
                                            "ban_reason": ''
                                        }
                                    }}
                                )
                                return False
                        except:
                            pass
                    
                    # User is banned
                    return True
        
        # User is not banned or doesn't exist
        return False
        
    except Exception as e:
        logger.error(f"Error checking ban status for user {user_id}: {e}")
        return False
