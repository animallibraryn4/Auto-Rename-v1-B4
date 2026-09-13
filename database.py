from pymongo import MongoClient, ASCENDING
from config import MONGO_URI, DB_NAME
import time

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db["users"]              # user profiles
likes = db["likes"]              # like records
matches = db["matches"]          # mutual matches
reports = db["reports"]          # reports
views = db["views"]              # already-seen profiles per user

# Indexes
users.create_index([("user_id", ASCENDING)], unique=True)
likes.create_index([("from_id", ASCENDING), ("to_id", ASCENDING)], unique=True)
views.create_index([("user_id", ASCENDING), ("seen_id", ASCENDING)], unique=True)


# ------------- USERS -------------

def get_user(user_id: int):
    return users.find_one({"user_id": user_id})


def create_or_update_user(user_id: int, **fields):
    users.update_one(
        {"user_id": user_id},
        {"$set": {**fields, "updated_at": time.time()},
         "$setOnInsert": {"created_at": time.time()}},
        upsert=True,
    )
    return get_user(user_id)


def delete_user(user_id: int):
    users.delete_one({"user_id": user_id})
    likes.delete_many({"$or": [{"from_id": user_id}, {"to_id": user_id}]})
    matches.delete_many({"$or": [{"user1": user_id}, {"user2": user_id}]})
    views.delete_many({"user_id": user_id})


def update_field(user_id: int, key: str, value):
    users.update_one({"user_id": user_id}, {"$set": {key: value}})


# ------------- DISCOVERY -------------

def get_candidates(user_id: int, gender_pref: str, city: str = None, country: str = None,
                   limit: int = 20):
    """
    Find profiles matching the user's preference.
    Priority: same city → same country → others.
    """
    seen = {v["seen_id"] for v in views.find({"user_id": user_id})}
    seen.add(user_id)

    gender_filter = {}
    if gender_pref in ("male", "female"):
        gender_filter["gender"] = gender_pref

    # same city first
    query_city = {"user_id": {"$nin": list(seen)},
                  "profile_complete": True, **gender_filter,
                  "city": {"$regex": f"^{city}$", "$options": "i"}} if city else None

    results = []
    if query_city:
        results.extend(list(users.find(query_city).limit(limit)))

    if len(results) < limit and country:
        query_country = {"user_id": {"$nin": list(seen) + [r["user_id"] for r in results]},
                         "profile_complete": True, **gender_filter,
                         "country": {"$regex": f"^{country}$", "$options": "i"}}
        results.extend(list(users.find(query_country).limit(limit - len(results))))

    if len(results) < limit:
        query_any = {"user_id": {"$nin": list(seen) + [r["user_id"] for r in results]},
                     "profile_complete": True, **gender_filter}
        results.extend(list(users.find(query_any).limit(limit - len(results))))

    return results


def mark_seen(user_id: int, seen_id: int):
    try:
        views.update_one(
            {"user_id": user_id, "seen_id": seen_id},
            {"$setOnInsert": {"ts": time.time()}},
            upsert=True,
        )
    except Exception:
        pass


# ------------- LIKES -------------

def add_like(from_id: int, to_id: int):
    try:
        likes.update_one(
            {"from_id": from_id, "to_id": to_id},
            {"$setOnInsert": {"ts": time.time()}},
            upsert=True,
        )
        return True
    except Exception:
        return False


def has_liked(from_id: int, to_id: int) -> bool:
    return likes.find_one({"from_id": from_id, "to_id": to_id}) is not None


def is_mutual(a: int, b: int) -> bool:
    return has_liked(a, b) and has_liked(b, a)


def get_pending_likes_for(user_id: int):
    """People who liked me but I haven't responded to yet."""
    # We track "response" by checking matches table
    liked_me = likes.find({"to_id": user_id})
    pending = []
    for l in liked_me:
        other = l["from_id"]
        m = matches.find_one({"$or": [
            {"user1": user_id, "user2": other},
            {"user1": other, "user2": user_id},
        ]})
        if not m:
            pending.append(other)
    return pending


# ------------- MATCHES -------------

def create_match(a: int, b: int):
    u1, u2 = sorted([a, b])
    matches.update_one(
        {"user1": u1, "user2": u2},
        {"$setOnInsert": {"ts": time.time()}},
        upsert=True,
    )


def get_matches(user_id: int):
    return list(matches.find({"$or": [{"user1": user_id}, {"user2": user_id}]}))


# ------------- REPORTS -------------

def add_report(from_id: int, to_id: int, reason: str = ""):
    reports.insert_one({
        "from_id": from_id,
        "to_id": to_id,
        "reason": reason,
        "ts": time.time(),
    })


# ------------- STATS -------------

def total_users():
    return users.count_documents({"profile_complete": True})
