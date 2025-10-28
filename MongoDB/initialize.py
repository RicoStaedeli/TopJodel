import json

# seed_likes.py
import random
from datetime import datetime, timezone
from typing import Iterable, List, Dict

from pymongo import UpdateOne, ASCENDING
from pymongo.errors import BulkWriteError

from MongoDB.connection import get_mongo_client
from MongoDB.mongo_repo import MongoPostsRepository

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


def _heavy_tailed_like_count(avg: int, max_cap: int) -> int:
    """
    Draw a like count with a heavy tail so a few posts are popular.
    Pareto with alpha ~ 2 gives a reasonable skew.
    """
    base = max(0, int(random.paretovariate(2.0) * (avg / 2)))
    return min(max_cap, base)

def _rand_users_for_post(k: int) -> List[int]:
    """
    Draw k unique user_ids in [MIN_USER_ID, MAX_USER_ID].
    If k > number of users, cap to number of users.
    """
    k = min(k, MAX_USER_ID - MIN_USER_ID + 1)
    return random.sample(range(MIN_USER_ID, MAX_USER_ID + 1), k)

def seed_likes():
    """
    Seed likes by calling the repository's add_like, not by writing directly.
    This keeps the posts.likes counter in sync and uses the unique index on (post_id, user_id).
    """
    client = get_mongo_client()
    db = client[DB_NAME]

    repo = MongoPostsRepository(db)  # ensures indexes on posts and post_likes

    existing_like_count = repo.likes.estimated_document_count()
    if existing_like_count > 0:
        print(f"Database already has {existing_like_count} likes, skipping seeding.")
        return

    # Stream post ids to avoid loading everything in memory
    cursor = repo.posts.find({}, {"_id": 1})

    total_planned = 0
    total_created = 0

    for doc in cursor:
        post_oid = doc["_id"]
        post_id = str(post_oid)

        # Decide how many users like this post
        k = _heavy_tailed_like_count(AVG_LIKES_PER_POST, MAX_LIKES_PER_POST)
        if k <= 0:
            continue

        planned_uids = _rand_users_for_post(k)
        total_planned += k

        created_for_post = 0
        for uid in planned_uids:
            # add_like returns True only when it actually created the like
            if repo.add_like(post_id, uid):
                created_for_post += 1
                total_created += 1

    print(f"Prepared ~{total_planned} likes, actually created {total_created}. Duplicates were skipped by add_like.")

    # Safety pass to ensure counters match reality if any drift occurred
    # This is optional since add_like already increments posts.likes.
    sync_like_counters(db)
    print("Like counters synced to posts.likes.")

def sync_like_counters(db):
    """
    Server-side aggregation to count likes per post, then write the number to posts.likes.
    Works with MongoDB 4.2+.
    """
    pipeline = [
        {"$group": {"_id": "$post_id", "count": {"$sum": 1}}},
        {
            "$merge": {
                "into": {"db": db.name, "coll": "posts"},
                "on": "_id",
                "whenMatched": [{"$set": {"likes": "$$new.count"}}],
                "whenNotMatched": "discard",
            }
        },
    ]
    db[LIKES_COLL].aggregate(pipeline, allowDiskUse=True)

def initialize_posts_col():
    """Initialize MongoDB with seed data from a JSON file using PostRepository.create_post()."""
    FILE_PATH = "MongoDB/import/init_posts.json"  # mounted path

    client = get_mongo_client()
    db = client[DB_NAME]
    repo = MongoPostsRepository(db)


    # Skip import if posts already exist
    db_initialized = repo.db_initialized()
    if db_initialized :
        print(f"Database already initialized — skipping import.")
        return

    # Load JSON
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)


    print(f"Loading {len(data)} posts from {FILE_PATH}...")
    inserted_count = 0

    for post in data:
        try:
            repo.create_post(
                user_id=post["user_id"],
                title=post["title"],
                text=post["text"],
                topics=post.get("topics", []),
            )
            inserted_count += 1
        except Exception as e:
            print(f"Skipping post '{post.get('title', 'unknown')}' — error: {e}")

    print(f"Inserted {inserted_count} posts into '{DB_NAME}.{POSTS_COLL}'")