import motor.motor_asyncio
import datetime
import logging
import time
from config import Config
from .utils import send_log

class Database:
    def __init__(self, uri, database_name):
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            self._client.server_info()
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise e
        self.codeflixbots = self._client[database_name]
        self.col = self.codeflixbots.user

    def new_user(self, id):
        return dict(
            _id=int(id),
            join_date=datetime.date.today().isoformat(),
            file_id=None,
            caption=None,
            metadata=True,
            metadata_code="Telegram : @Animelibraryn4",
            format_template=None,
            thumbnails={},
            temp_quality=None,
            use_global_thumb=False,
            global_thumb=None,
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.date.max.isoformat(),
                ban_reason=''
            ),
            # Metadata fields
            title='Encoded by @Animelibraryn4',
            author='@Animelibraryn4',
            artist='@Animelibraryn4',
            audio='By @Animelibraryn4',
            subtitle='By @Animelibraryn4',
            video='Encoded By @Animelibraryn4',
            media_type=None,
            # New fields for sequence and mode
            rename_mode="file",  # "file" or "caption"
            mode="file_mode",    # "file_mode" or "caption_mode"
            verify_status=0,     # Timestamp of last verification
            last_sequence_time=0, # Timestamp of last sequence operation
            sequence_count=0     # Count of sequence operations
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            try:
                await self.col.insert_one(user)
                await send_log(b, u)
            except Exception as e:
                logging.error(f"Error adding user {u.id}: {e}")

    async def is_user_exist(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return bool(user)
        except Exception as e:
            logging.error(f"Error checking if user {id} exists: {e}")
            return False

    async def total_users_count(self):
        try:
            count = await self.col.count_documents({})
            return count
        except Exception as e:
            logging.error(f"Error counting users: {e}")
            return 0

    async def get_all_users(self):
        try:
            all_users = self.col.find({})
            return all_users
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return None

    async def delete_user(self, user_id):
        try:
            await self.col.delete_many({"_id": int(user_id)})
        except Exception as e:
            logging.error(f"Error deleting user {user_id}: {e}")

    async def set_thumbnail(self, id, file_id):
        try:
            await self.col.update_one({"_id": int(id)}, {"$set": {"file_id": file_id}})
        except Exception as e:
            logging.error(f"Error setting thumbnail for user {id}: {e}")

    async def get_thumbnail(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("file_id", None) if user else None
        except Exception as e:
            logging.error(f"Error getting thumbnail for user {id}: {e}")
            return None

    async def set_caption(self, id, caption):
        try:
            await self.col.update_one({"_id": int(id)}, {"$set": {"caption": caption}})
        except Exception as e:
            logging.error(f"Error setting caption for user {id}: {e}")

    async def get_caption(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("caption", None) if user else None
        except Exception as e:
            logging.error(f"Error getting caption for user {id}: {e}")
            return None

    async def set_format_template(self, id, format_template):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"format_template": format_template}}
            )
        except Exception as e:
            logging.error(f"Error setting format template for user {id}: {e}")

    async def get_format_template(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("format_template", None) if user else None
        except Exception as e:
            logging.error(f"Error getting format template for user {id}: {e}")
            return None

    async def set_media_preference(self, id, media_type):
        try:
            await self.col.update_one(
                {"_id": int(id)}, {"$set": {"media_type": media_type}}
            )
        except Exception as e:
            logging.error(f"Error setting media preference for user {id}: {e}")

    async def get_media_preference(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("media_type", None) if user else None
        except Exception as e:
            logging.error(f"Error getting media preference for user {id}: {e}")
            return None

    async def get_metadata(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('metadata', "Off")

    async def set_metadata(self, user_id, metadata):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'metadata': metadata}})

    async def get_title(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('title', 'Encoded by @Animelibraryn4')

    async def set_title(self, user_id, title):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'title': title}})

    async def get_author(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('author', '@Animelibraryn4')

    async def set_author(self, user_id, author):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'author': author}})

    async def get_artist(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('artist', '@Animelibraryn4')

    async def set_artist(self, user_id, artist):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'artist': artist}})

    async def get_audio(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('audio', 'By @Animelibraryn4')

    async def set_audio(self, user_id, audio):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'audio': audio}})

    async def get_subtitle(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('subtitle', "By @Animelibraryn4")

    async def set_subtitle(self, user_id, subtitle):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'subtitle': subtitle}})

    async def get_video(self, user_id):
        user = await self.col.find_one({'_id': int(user_id)})
        return user.get('video', 'Encoded By @Animelibraryn4')

    async def set_video(self, user_id, video):
        await self.col.update_one({'_id': int(user_id)}, {'$set': {'video': video}})

    # Quality Thumbnail Methods
    async def set_quality_thumbnail(self, id, quality, file_id):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$set": {f"thumbnails.{quality}": file_id}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error setting thumbnail for quality {quality} for user {id}: {e}")

    async def get_quality_thumbnail(self, id, quality):
        try:
            user = await self.col.find_one({"_id": int(id)})
            if user and "thumbnails" in user:
                return user["thumbnails"].get(quality)
            return None
        except Exception as e:
            logging.error(f"Error getting thumbnail for quality {quality} for user {id}: {e}")
            return None

    async def get_all_thumbnails(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            if user and "thumbnails" in user:
                return user["thumbnails"]
            return {}
        except Exception as e:
            logging.error(f"Error getting all thumbnails for user {id}: {e}")
            return {}

    # Temporary quality storage methods
    async def set_temp_quality(self, id, quality):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$set": {"temp_quality": quality}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error setting temp quality for user {id}: {e}")

    async def get_temp_quality(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("temp_quality") if user else None
        except Exception as e:
            logging.error(f"Error getting temp quality for user {id}: {e}")
            return None

    async def clear_temp_quality(self, id):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$unset": {"temp_quality": ""}}
            )
        except Exception as e:
            logging.error(f"Error clearing temp quality for user {id}: {e}")

    # Global Thumbnail Methods
    async def set_global_thumb(self, id, file_id):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$set": {"global_thumb": file_id}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error setting global thumbnail for user {id}: {e}")

    async def get_global_thumb(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("global_thumb") if user else None
        except Exception as e:
            logging.error(f"Error getting global thumbnail for user {id}: {e}")
            return None

    async def toggle_global_thumb(self, id, status: bool):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$set": {"use_global_thumb": status}},
                upsert=True
            )
        except Exception as e:
            logging.error(f"Error toggling global thumb for user {id}: {e}")

    async def is_global_thumb_enabled(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("use_global_thumb", False) if user else False
        except Exception as e:
            logging.error(f"Error checking global thumb status for user {id}: {e}")
            return False

    # Verification Methods
    async def get_verify_status(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            if user:
                return user.get("verify_status", 0)
            return 0
        except Exception as e:
            logging.error(f"Error getting verify status for user {id}: {e}")
            return 0

    async def set_verify_status(self, id, verify_status):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$set": {"verify_status": verify_status}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting verify status for user {id}: {e}")
            return False

    async def delete_verify_status(self, id):
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$unset": {"verify_status": ""}}
            )
            return True
        except Exception as e:
            logging.error(f"Error deleting verify status for user {id}: {e}")
            return False

    # Mode Methods (for auto rename)
    async def get_mode(self, user_id):
        """Get user's mode preference (file_mode or caption_mode)"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("mode", "file_mode")  # Default to file_mode
        except Exception as e:
            logging.error(f"Error getting mode for user {user_id}: {e}")
            return "file_mode"

    async def set_mode(self, user_id, mode):
        """Set user's mode preference"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"mode": mode}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting mode for user {user_id}: {e}")
            return False

    # Rename Mode Methods (for sequence - legacy support)
    async def get_rename_mode(self, id):
        """Get user's rename mode preference (file or caption)"""
        try:
            user = await self.col.find_one({"_id": int(id)})
            return user.get("rename_mode", "file")  # Default to file
        except Exception as e:
            logging.error(f"Error getting rename mode for user {id}: {e}")
            return "file"

    async def set_rename_mode(self, id, mode):
        """Set user's rename mode preference"""
        try:
            await self.col.update_one(
                {"_id": int(id)},
                {"$set": {"rename_mode": mode}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting rename mode for user {id}: {e}")
            return False

    async def toggle_rename_mode(self, id):
        """Toggle between file and caption mode"""
        try:
            current = await self.get_rename_mode(id)
            new_mode = "caption" if current == "file" else "file"
            await self.set_rename_mode(id, new_mode)
            return new_mode
        except Exception as e:
            logging.error(f"Error toggling rename mode for user {id}: {e}")
            return "file"

    # Sequence Tracking Methods
    async def get_last_sequence_time(self, user_id):
        """Get last sequence operation time"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("last_sequence_time", 0)
        except Exception as e:
            logging.error(f"Error getting last sequence time for user {user_id}: {e}")
            return 0

    async def set_last_sequence_time(self, user_id, timestamp=None):
        """Set last sequence operation time"""
        try:
            if timestamp is None:
                timestamp = int(time.time())
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"last_sequence_time": timestamp}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting last sequence time for user {user_id}: {e}")
            return False

    async def get_sequence_count(self, user_id):
        """Get sequence operation count"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("sequence_count", 0)
        except Exception as e:
            logging.error(f"Error getting sequence count for user {user_id}: {e}")
            return 0

    async def increment_sequence_count(self, user_id):
        """Increment sequence operation count"""
        try:
            current_count = await self.get_sequence_count(user_id)
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"sequence_count": current_count + 1}},
                upsert=True
            )
            return current_count + 1
        except Exception as e:
            logging.error(f"Error incrementing sequence count for user {user_id}: {e}")
            return 0

    # Premium/Plan Methods
    async def get_premium_status(self, user_id):
        """Get user's premium status"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("premium_status", "free")
        except Exception as e:
            logging.error(f"Error getting premium status for user {user_id}: {e}")
            return "free"

    async def set_premium_status(self, user_id, status):
        """Set user's premium status"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"premium_status": status}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting premium status for user {user_id}: {e}")
            return False

    async def get_premium_expiry(self, user_id):
        """Get premium expiry timestamp"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("premium_expiry", 0)
        except Exception as e:
            logging.error(f"Error getting premium expiry for user {user_id}: {e}")
            return 0

    async def set_premium_expiry(self, user_id, expiry_timestamp):
        """Set premium expiry timestamp"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"premium_expiry": expiry_timestamp}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting premium expiry for user {user_id}: {e}")
            return False

    async def is_premium_active(self, user_id):
        """Check if user has active premium"""
        try:
            expiry = await self.get_premium_expiry(user_id)
            if expiry == 0:
                return False
            return int(time.time()) < expiry
        except Exception as e:
            logging.error(f"Error checking premium status for user {user_id}: {e}")
            return False

    # Watermark Methods
    async def get_watermark(self, user_id):
        """Get user's watermark text"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("watermark", None)
        except Exception as e:
            logging.error(f"Error getting watermark for user {user_id}: {e}")
            return None

    async def set_watermark(self, user_id, watermark_text):
        """Set user's watermark text"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"watermark": watermark_text}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting watermark for user {user_id}: {e}")
            return False

    async def delete_watermark(self, user_id):
        """Delete user's watermark"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$unset": {"watermark": ""}}
            )
            return True
        except Exception as e:
            logging.error(f"Error deleting watermark for user {user_id}: {e}")
            return False

    # Ban/Unban Methods
    # Ban/Unban Methods
    async def ban_user(self, user_id, duration_hours=0, reason=""):
        """Ban a user"""
        try:
            ban_data = {
                "is_banned": True,
                "ban_duration": duration_hours,
                "banned_on": datetime.date.today().isoformat(),
                "ban_reason": reason
            }
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"ban_status": ban_data}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error banning user {user_id}: {e}")
            return False

    async def unban_user(self, user_id):
        """Unban a user"""
        try:
            ban_data = {
                "is_banned": False,
                "ban_duration": 0,
                "banned_on": datetime.date.max.isoformat(),
                "ban_reason": ''
            }
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"ban_status": ban_data}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error unbanning user {user_id}: {e}")
            return False

    async def is_user_banned(self, user_id):
        """Check if user is banned"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            if user and "ban_status" in user:
                return user["ban_status"].get("is_banned", False)
            return False
        except Exception as e:
            logging.error(f"Error checking ban status for user {user_id}: {e}")
            return False

    # Statistics Methods
    async def get_user_stats(self, user_id):
        """Get comprehensive user statistics"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            if not user:
                return None
            
            stats = {
                "join_date": user.get("join_date", "Unknown"),
                "rename_mode": user.get("rename_mode", "file"),
                "mode": user.get("mode", "file_mode"),
                "sequence_count": user.get("sequence_count", 0),
                "premium_status": user.get("premium_status", "free"),
                "premium_active": await self.is_premium_active(user_id),
                "premium_expiry": user.get("premium_expiry", 0),
                "verify_status": user.get("verify_status", 0),
                "is_banned": user.get("ban_status", {}).get("is_banned", False),
                "has_watermark": bool(user.get("watermark", None)),
                "has_caption": bool(user.get("caption", None)),
                "has_thumbnail": bool(user.get("file_id", None)),
                "format_template": user.get("format_template", "Not set"),
                "media_preference": user.get("media_type", "Not set"),
                "metadata_enabled": user.get("metadata", True)
            }
            
            return stats
        except Exception as e:
            logging.error(f"Error getting user stats for user {user_id}: {e}")
            return None

    async def get_all_user_ids(self):
        """Get all user IDs from database"""
        try:
            user_ids = []
            async for user in self.col.find({}, {"_id": 1}):
                user_ids.append(user["_id"])
            return user_ids
        except Exception as e:
            logging.error(f"Error getting all user IDs: {e}")
            return []

    async def get_active_users_count(self, days=7):
        """Count users active in last N days"""
        try:
            cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
            count = await self.col.count_documents({
                "$or": [
                    {"verify_status": {"$gte": cutoff_time}},
                    {"last_sequence_time": {"$gte": cutoff_time}}
                ]
            })
            return count
        except Exception as e:
            logging.error(f"Error counting active users: {e}")
            return 0

    # Cleanup Methods
    async def cleanup_inactive_users(self, days=30):
        """Remove users inactive for N days"""
        try:
            cutoff_time = int(time.time()) - (days * 24 * 60 * 60)
            result = await self.col.delete_many({
                "verify_status": {"$lt": cutoff_time},
                "last_sequence_time": {"$lt": cutoff_time},
                "premium_expiry": {"$lt": cutoff_time}
            })
            return result.deleted_count
        except Exception as e:
            logging.error(f"Error cleaning up inactive users: {e}")
            return 0

    async def reset_user_data(self, user_id):
        """Reset user's data (for testing or cleanup)"""
        try:
            # Keep only essential fields
            reset_data = {
                "caption": None,
                "format_template": None,
                "thumbnails": {},
                "global_thumb": None,
                "use_global_thumb": False,
                "watermark": None,
                "last_sequence_time": 0,
                "sequence_count": 0
            }
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": reset_data}
            )
            return True
        except Exception as e:
            logging.error(f"Error resetting user data for user {user_id}: {e}")
            return False

# Initialize database connection
codeflixbots = Database(Config.DB_URL, Config.DB_NAME)
