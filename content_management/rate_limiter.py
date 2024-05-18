from datetime import timedelta

from redis import Redis


class BaseRateLimiter:
    def is_limited(self, key: str) -> bool:
        raise NotImplementedError


class TokenBucketRateLimiter(BaseRateLimiter):
    conn: Redis
    limit_count: int
    limit_period: timedelta

    def __init__(
        self,
        conn: Redis,
        limit_count: int = 100,
        limit_period: timedelta = timedelta(minutes=1),
    ):
        # TODO: limit count and period must be configurable from admin panel,
        # some packages like constance are suitable for this use case
        self.conn = conn
        self.limit_count = limit_count
        self.limit_period = limit_period

    def is_limited(self, key: str) -> bool:
        if self.conn.setnx(key, self.limit_count):
            self.conn.expire(key, int(self.limit_period.total_seconds()))
        bucket_val = self.conn.get(key)
        if bucket_val and int(bucket_val) > 0:
            self.conn.decrby(key, 1)
            return False
        return True
