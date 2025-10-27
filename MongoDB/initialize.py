import json

# seed_likes.py
import random
from datetime import datetime, timezone
from typing import Iterable, List, Dict

from pymongo import UpdateOne, ASCENDING
from pymongo.errors import BulkWriteError

from MongoDB.connection import get_mongo_client

DB_NAME = "appdb"
POSTS_COLL = "posts"
LIKES_COLL = "post_likes"

# Adjust to your SQL users range
MIN_USER_ID = 1
MAX_USER_ID = 80

# Controls how many likes per post on average
AVG_LIKES_PER_POST = 10        # rough average
MAX_LIKES_PER_POST = 120       # hard cap just in case
BATCH_SIZE = 5000              # bulk write batch size


def heavy_tailed_like_count(avg: int, max_cap: int) -> int:
    """
    Draw a like count with a heavy tail so a few posts are popular.
    Pareto with alpha ~ 2 gives a reasonable skew.
    """
    # Base around avg with randomness
    base = max(0, int(random.paretovariate(2.0) * (avg / 2)))
    return min(max_cap, base)


def rand_users_for_post(k: int) -> List[int]:
    """
    Draw k unique user_ids in [MIN_USER_ID, MAX_USER_ID].
    If k > number of users, we cap to number of users.
    """
    k = min(k, MAX_USER_ID - MIN_USER_ID + 1)
    return random.sample(range(MIN_USER_ID, MAX_USER_ID + 1), k)


def ensure_indexes(db):
    posts = db[POSTS_COLL]
    likes = db[LIKES_COLL]
    posts.create_index([("created_at", ASCENDING)])
    posts.create_index([("user_id", ASCENDING)])
    likes.create_index([("post_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    likes.create_index([("post_id", ASCENDING)])


def seed_likes():
    client = get_mongo_client()
    db = client[DB_NAME]
    posts = db[POSTS_COLL]
    likes = db[LIKES_COLL]

    ensure_indexes(db)

    like_count = likes.count_documents({})
    if like_count > 0:
        print(f"ℹ️  Database already has {like_count} likes — skipping seeding.")
        return

    # Stream post ids to avoid loading everything in memory
    cursor = posts.find({}, {"_id": 1})
    ops: List[UpdateOne] = []
    total_planned = 0

    for doc in cursor:
        post_id = doc["_id"]

        # Decide how many users like this post
        k = heavy_tailed_like_count(AVG_LIKES_PER_POST, MAX_LIKES_PER_POST)
        if k <= 0:
            continue

        for uid in rand_users_for_post(k):
            # Upsert makes this idempotent
            ops.append(
                UpdateOne(
                    {"post_id": post_id, "user_id": uid},
                    {"$setOnInsert": {"post_id": post_id, "user_id": uid, "created_at": datetime.now(timezone.utc)}},
                    upsert=True,
                )
            )
        total_planned += k

        # Flush in batches
        if len(ops) >= BATCH_SIZE:
            _flush(likes, ops)

    # Final flush
    if ops:
        _flush(likes, ops)

    print(f"Prepared ~{total_planned} likes (duplicates skipped via upsert).")

    # Sync the denormalized counter on posts
    sync_like_counters(db)
    print("Like counters synced to posts.likes.")


def _flush(likes_coll, ops: List[UpdateOne]):
    try:
        res = likes_coll.bulk_write(ops, ordered=False)
        inserted = (res.upserted_count or 0) + (res.inserted_count or 0)
        print(f"bulk_write: upserted or inserted {inserted}, matched {res.matched_count}")
    except BulkWriteError as e:
        # Upserts can still race, but ordered=False keeps it fast
        details = e.details or {}
        n = details.get("nInserted", 0)
        print(f"bulk_write completed with duplicates, inserted {n}")
    finally:
        ops.clear()


def sync_like_counters(db):
    """
    Server-side aggregation to count likes per post, then write the number to posts.likes.
    Requires MongoDB 4.2+.
    """
    pipeline = [
        {"$group": {"_id": "$post_id", "count": {"$sum": 1}}},
        {
            "$merge": {
                "into": {"db": DB_NAME, "coll": POSTS_COLL},
                "on": "_id",
                "whenMatched": [
                    {"$set": {"likes": "$$new.count"}}
                ],
                "whenNotMatched": "discard",
            }
        },
    ]
    db[LIKES_COLL].aggregate(pipeline, allowDiskUse=True)

def initialize_posts_col():
    """Initialize MongoDB with seed data from a JSON file."""
    FILE_PATH = "MongoDB/import/init_posts.json"  # mounted path

    client = get_mongo_client()
    db = client[DB_NAME]
    posts = db[POSTS_COLL]

    # Skip import if posts already exist
    existing_count = posts.count_documents({})
    if existing_count > 0:
        print(f"ℹ️  Database already has {existing_count} posts — skipping import.")
        return

    # Read JSON
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📦 Loading {len(data)} posts from {FILE_PATH}...")
    try:
        result = posts.insert_many(data, ordered=False)
        print(f"Inserted {len(result.inserted_ids)} posts into '{DB_NAME}.{POSTS_COLL}'")
    except BulkWriteError as e:
        inserted = e.details.get("nInserted", 0)
        print(f"Warning: Inserted {inserted} posts before duplicate error.")
    except Exception as e:
        print(f"Error: Import failed: {e}")