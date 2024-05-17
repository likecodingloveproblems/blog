from __future__ import annotations

import redis.utils
from django.db.models import Count, OuterRef, Avg
from django.db.models.functions import Coalesce
from redis import Redis

from content_management.models import Content, Like


class BaseCache:
    conn: Redis

    def __init__(self, conn: Redis):
        '''Get a redis connection session'''
        self.conn = conn

    def _get_data(self):
        '''It will return all the database related data'''
        raise NotImplementedError

    def get_key(self, *args, **kwargs):
        '''Get data key to be used in cache'''
        raise NotImplementedError

    def get_value(self, data):
        '''Get value to be set in cache'''
        raise NotImplementedError

    def _build(self, data):
        '''Set all data to the cache'''
        pipe = self.conn.pipeline()
        for row in data:
            key = self.get_key(row)
            value = self.get_value(row)
            pipe.hset(key, mapping=value)
        pipe.execute()

    def build(self):
        '''It will build cache from related database tables'''
        data = self._get_data()
        return self._build(data)

    def list(self, ids: list[int]) -> list[dict]:
        '''It will return a list of data related to a list of ids'''
        pipe = self.conn.pipeline()
        for id_ in ids:
            key = self.get_key(id_=id_)
            pipe.hgetall(key)
        data = pipe.execute()
        # filter empty values
        data = filter(lambda item: item, data)
        return data


class ContentCache(BaseCache):
    '''This Cache will store content and content's like data'''

    def __init__(self, conn: Redis):
        super().__init__(conn)

    def get_key(self, content: dict | None = None, id_: int | None = None) -> str:
        if content and content.get('id'):
            id_ = content['id']
        return f'content:{id_}'

    def get_value(self, content: dict) -> dict:
        return content

    def _get_data(self):
        """Get content data from database"""
        likes = Like.objects.filter(content_id=OuterRef('id')).values('content_id')
        likes_count = likes.annotate(count=Count('user_id', distinct=True)).values('count')
        likes_avg = likes.annotate(avg=Avg('value')).values('avg')
        contents = Content.objects.annotate(
            likes_count=Coalesce(likes_count, 0),
            likes_avg=Coalesce(likes_avg, 0.0),
        ).values('id', 'title', 'likes_count', 'likes_avg')
        return contents

    def content_liked(self, like: Like):
        """Update content like related data
        increase like count by one
        update like avg with new like value
        """
        past_count = int(self.conn.hget(self.get_key(id_=like.content_id), 'likes_count') or 0)
        past_avg = int(self.conn.hget(self.get_key(id_=like.content_id), 'likes_avg') or 0)
        new_avg = (past_avg * past_count + like.value) / (past_count + 1)

        self.conn.hincrby(self.get_key(id_=like.content_id), "likes_count")
        self.conn.hset(self.get_key(id_=like.content_id), 'likes_avg', new_avg)

    def like_value_updated(self, like: Like):
        """Update content like related data
        increase like count by one
        update like avg with new like value
        """
        past_value = like.initial_value('value')
        new_value = like.value
        count = int(self.conn.hget(self.get_key(id_=like.content_id), 'likes_count') or 0)
        avg_delta = (new_value - past_value) / count
        self.conn.hincrby(self.get_key(id_=like.content_id), 'likes_avg', avg_delta)
