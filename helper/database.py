import motor.motor_asyncio
import datetime
import logging
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
        self.n4bots = self._client[database_name]
        self.col = self.n4bots.user

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
            use_global_thumb=False,  # New field for global thumbnail toggle
            global_thumb=None,       # Stores the global thumbnail file_id
            ban_status=dict(
                is_banned=False,
                ban_duration=0,
                banned_on=datetime.date.max.isoformat(),
                ban_reason=''
            ),
            # Preserving all existing metadata fields
            title='Encoded by @N4_Bots',
            author='@N4_Bots',
            artist='@N4_Bots',
            audio='By @N4_Bots',
            subtitle='By @N4_Bots',
            video='Encoded By @N4_Bots',
            media_type=None,
            metadata_profile=1  # Default to profile 1
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

    async def get_verify_status(self, id):
        try:
            user = await self.col.find_one({"_id": int(id)})
            if user:
                # Check if user has verify_status field, if not return 0
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

    # Sequence methods
    async def set_sequence_mode(self, user_id, mode):
        """Set user's sequence mode preference"""
        try:
            await self.col.update_one(
            {"_id": int(user_id)},
            {"$set": {"sequence_mode": mode}},
            upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting sequence mode for user {user_id}: {e}")
            return False

    async def get_sequence_mode(self, user_id):
        """Get user's sequence mode preference"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("sequence_mode", "per_ep")  # Default to episode flow
        except Exception as e:
            logging.error(f"Error getting sequence mode for user {user_id}: {e}")
            return "per_ep"

    # Ban-related methods
    async def ban_user(self, user_id, duration=0, reason=''):
        """Ban a user"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {
                    "ban_status": {
                        "is_banned": True,
                        "ban_duration": duration,
                        "banned_on": datetime.date.today().isoformat(),
                        "ban_reason": reason
                    }
                }}
            )
            return True
        except Exception as e:
            logging.error(f"Error banning user {user_id}: {e}")
            return False

    async def unban_user(self, user_id):
        """Unban a user"""
        try:
            await self.col.update_one(
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
            return True
        except Exception as e:
            logging.error(f"Error unbanning user {user_id}: {e}")
            return False

    async def get_ban_status(self, user_id):
        """Get ban status of a user"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            if user:
                return user.get("ban_status", {
                    "is_banned": False,
                    "ban_duration": 0,
                    "banned_on": datetime.date.max.isoformat(),
                    "ban_reason": ''
                })
            return None
        except Exception as e:
            logging.error(f"Error getting ban status for user {user_id}: {e}")
            return None

    async def get_banned_users(self):
        """Get all banned users"""
        try:
            banned_users = []
            async for user in self.col.find({"ban_status.is_banned": True}):
                banned_users.append(user)
            return banned_users
        except Exception as e:
            logging.error(f"Error getting banned users: {e}")
            return []

    # Profile Support Methods
    async def get_current_profile(self, user_id):
        """Get user's current metadata profile (1 or 2)"""
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            return user.get("metadata_profile", 1)  # Default to profile 1
        except Exception as e:
            logging.error(f"Error getting metadata profile for user {user_id}: {e}")
            return 1

    async def set_current_profile(self, user_id, profile_num):
        """Set user's current metadata profile"""
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {"metadata_profile": profile_num}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting metadata profile for user {user_id}: {e}")
            return False

    async def get_metadata_field_with_profile(self, user_id, field, profile_num=None):
        """Get metadata field with profile support"""
        if profile_num is None:
            profile_num = await self.get_current_profile(user_id)
        
        # Field names with profile suffix
        profile_fields = {
            "title": f"title_profile_{profile_num}",
            "author": f"author_profile_{profile_num}",
            "artist": f"artist_profile_{profile_num}",
            "audio": f"audio_profile_{profile_num}",
            "subtitle": f"subtitle_profile_{profile_num}",
            "video": f"video_profile_{profile_num}"
        }
        
        field_key = profile_fields.get(field)
        if not field_key:
            return None
        
        try:
            user = await self.col.find_one({"_id": int(user_id)})
            if user and field_key in user:
                return user.get(field_key)
            else:
                # Fallback to default field if profile field doesn't exist
                method_name = f"get_{field}"
                method = getattr(self, method_name, None)
                if method:
                    return await method(user_id)
            return None
        except Exception as e:
            logging.error(f"Error getting {field} for profile {profile_num} for user {user_id}: {e}")
            return None

    async def set_metadata_field_with_profile(self, user_id, field, value, profile_num=None):
        """Set metadata field with profile support"""
        if profile_num is None:
            profile_num = await self.get_current_profile(user_id)
        
        # Field names with profile suffix
        profile_fields = {
            "title": f"title_profile_{profile_num}",
            "author": f"author_profile_{profile_num}",
            "artist": f"artist_profile_{profile_num}",
            "audio": f"audio_profile_{profile_num}",
            "subtitle": f"subtitle_profile_{profile_num}",
            "video": f"video_profile_{profile_num}"
        }
        
        field_key = profile_fields.get(field)
        if not field_key:
            return False
        
        try:
            await self.col.update_one(
                {"_id": int(user_id)},
                {"$set": {field_key: value}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting {field} for profile {profile_num} for user {user_id}: {e}")
            return False

    async def copy_profile_to_profile(self, user_id, from_profile, to_profile):
        """Copy all metadata fields from one profile to another"""
        try:
            fields = ["title", "author", "artist", "audio", "subtitle", "video"]
            
            for field in fields:
                # Get value from source profile
                from_field = f"{field}_profile_{from_profile}"
                user = await self.col.find_one({"_id": int(user_id)})
                value = user.get(from_field) if user else None
                
                if value is None:
                    # If source profile field doesn't exist, get default
                    method_name = f"get_{field}"
                    method = getattr(self, method_name, None)
                    if method:
                        value = await method(user_id)
                
                # Set to target profile
                to_field = f"{field}_profile_{to_profile}"
                await self.col.update_one(
                    {"_id": int(user_id)},
                    {"$set": {to_field: value}},
                    upsert=True
                )
            return True
        except Exception as e:
            logging.error(f"Error copying profile {from_profile} to {to_profile} for user {user_id}: {e}")
            return False

    async def get_all_profiles_summary(self, user_id):
        """Get summary of both profiles"""
        summary = {}
        
        for profile_num in [1, 2]:
            profile_data = {}
            for field in ["title", "author", "artist", "audio", "subtitle", "video"]:
                value = await self.get_metadata_field_with_profile(user_id, field, profile_num)
                profile_data[field] = value
            summary[f"profile_{profile_num}"] = profile_data
        
        return summary

# Initialize database connection
n4bots = Database(Config.DB_URL, Config.DB_NAME)
