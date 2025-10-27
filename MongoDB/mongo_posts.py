# repositories/mongo_posts.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from pymongo.database import Database
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING, ReturnDocument, errors
from bson import ObjectId

UserId = int

@dataclass(frozen=True)
class Post:
    id: str
    user_id: UserId
    title: str
    text: str
    topics: List[str]
    likes: int
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_doc(doc: Dict[str, Any]) -> "Post":
        return Post(
            id=str(doc["_id"]),
            user_id=doc["user_id"],           # int in Mongo
            title=doc["title"],
            text=doc["text"],
            topics=doc.get("topics", []),
            likes=int(doc.get("likes", 0)),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at", doc["created_at"]),
        )

class PostNotFound(Exception): ...
class NotOwner(Exception): ...

class MongoPostsRepository:
    """
    Collections
      - posts: one document per post
      - post_likes: one document per (post_id, user_id)

    Field types
      - posts.user_id: int  (matches SQL users.id)
      - post_likes.user_id: int
    """

    def __init__(self, db: Database):
        self.db: Database = db
        self.posts: Collection = self.db["posts"]
        self.likes: Collection = self.db["post_likes"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        # posts
        self.posts.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        self.posts.create_index([("topics", ASCENDING)])
        self.posts.create_index([("created_at", DESCENDING)])
        # likes
        self.likes.create_index([("post_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
        self.likes.create_index([("post_id", ASCENDING)])

        # Schema validation - user_id must be int
        try:
            self.db.command({
                "collMod": "posts",
                "validator": {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["user_id", "title", "text", "created_at"],
                        "properties": {
                            "user_id": {"bsonType": "int"},
                            "title": {"bsonType": "string", "minLength": 1},
                            "text": {"bsonType": "string"},
                            "topics": {"bsonType": ["array"], "items": {"bsonType": "string"}},
                            "likes": {"bsonType": ["int", "long"], "minimum": 0},
                            "created_at": {"bsonType": "date"},
                            "updated_at": {"bsonType": "date"},
                        }
                    }
                },
                "validationLevel": "moderate",
            })
        except errors.OperationFailure:
            pass

    # Helpers
    @staticmethod
    def _oid(id_or_oid: Any) -> ObjectId:
        if isinstance(id_or_oid, ObjectId):
            return id_or_oid
        try:
            return ObjectId(str(id_or_oid))
        except Exception as e:
            raise PostNotFound("invalid post id") from e

    # CRUD
    def create_post(self, user_id: UserId, title: str, text: str, topics: Optional[List[str]] = None) -> str:
        now = datetime.now(timezone.utc)
        doc = {
            "user_id": int(user_id),
            "title": title,
            "text": text,
            "topics": topics or [],
            "likes": 0,
            "created_at": now,
            "updated_at": now,
        }
        res = self.posts.insert_one(doc)
        return str(res.inserted_id)

    def delete_post(self, post_id: str, user_id: Optional[UserId] = None) -> bool:
        oid = self._oid(post_id)
        query: Dict[str, Any] = {"_id": oid}
        if user_id is not None:
            query["user_id"] = int(user_id)

        res = self.posts.delete_one(query)
        if res.deleted_count == 0:
            if user_id is not None:
                exists = self.posts.find_one({"_id": oid}, {"_id": 1, "user_id": 1})
                if exists:
                    raise NotOwner("user is not the owner of the post")
            raise PostNotFound("post not found")

        self.likes.delete_many({"post_id": oid})
        return True

    def edit_post(
        self,
        post_id: str,
        user_id: Optional[UserId],
        *,
        title: Optional[str] = None,
        text: Optional[str] = None,
    ) -> Post:
        oid = self._oid(post_id)
        to_set: Dict[str, Any] = {}
        if title is not None:
            to_set["title"] = title
        if text is not None:
            to_set["text"] = text
        if not to_set:
            doc = self.posts.find_one({"_id": oid})
            if not doc:
                raise PostNotFound("post not found")
            return Post.from_doc(doc)

        query: Dict[str, Any] = {"_id": oid}
        if user_id is not None:
            query["user_id"] = int(user_id)

        doc = self.posts.find_one_and_update(
            query,
            {"$set": {**to_set, "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            if user_id is not None:
                exists = self.posts.find_one({"_id": oid}, {"_id": 1, "user_id": 1})
                if exists:
                    raise NotOwner("user is not the owner of the post")
            raise PostNotFound("post not found")
        return Post.from_doc(doc)

    def get_posts_by_user(self, user_id: UserId, limit: int = 20, skip: int = 0) -> List[Post]:
        cursor = self.posts.find({"user_id": int(user_id)}).sort("created_at", DESCENDING).skip(skip).limit(limit)
        return [Post.from_doc(d) for d in cursor]

    # Topics
    def update_topics(self, post_id: str, user_id: Optional[UserId], topics: List[str]) -> Post:
        oid = self._oid(post_id)
        query: Dict[str, Any] = {"_id": oid}
        if user_id is not None:
            query["user_id"] = int(user_id)

        doc = self.posts.find_one_and_update(
            query,
            {"$set": {"topics": list(dict.fromkeys(topics)), "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            if user_id is not None:
                exists = self.posts.find_one({"_id": oid}, {"_id": 1, "user_id": 1})
                if exists:
                    raise NotOwner("user is not the owner of the post")
            raise PostNotFound("post not found")
        return Post.from_doc(doc)

    # Likes
    def add_like(self, post_id: str, user_id: UserId) -> bool:
        """
        Add a like to a post by a user. If a user has already liked the post, do nothing and return false.
        :param post_id:
        :param user_id:
        :return: true if like was created, false if it already existed
        """
        oid = self._oid(post_id)
        try:
            res = self.likes.update_one(
                {"post_id": oid, "user_id": int(user_id)},
                {"$setOnInsert": {
                    "post_id": oid,
                    "user_id": int(user_id),
                    "created_at": datetime.now(timezone.utc)
                }},
                upsert=True,
            )
        except errors.DuplicateKeyError:
            return False

        created = res.upserted_id is not None
        if created:
            self.posts.update_one({"_id": oid}, {"$inc": {"likes": 1}})
        return created

    def get_like_count(self, post_id: str) -> int:
        oid = self._oid(post_id)
        doc = self.posts.find_one({"_id": oid}, {"likes": 1})
        if doc and "likes" in doc:
            return int(doc.get("likes", 0))
        cnt = self.likes.count_documents({"post_id": oid})
        self.posts.update_one({"_id": oid}, {"$set": {"likes": int(cnt)}})
        return int(cnt)

    def get_post_by_id(self, post_id: str) -> Post:
        """
        Fetch a single post by its Mongo ObjectId string.
        Raises PostNotFound if not found.
        """
        oid = self._oid(post_id)
        doc = self.posts.find_one({"_id": oid})
        if not doc:
            raise PostNotFound(f"post {post_id} not found")
        return Post.from_doc(doc)