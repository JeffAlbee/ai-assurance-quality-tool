import redis
import logging

def get_redis_client():
    try:
        client = redis.Redis(
            host="redis",
            port=6379,
            db=0,
            decode_responses=True
        )
        client.ping()
        logging.info("✅ Redis client connected successfully")
        return client
    except redis.ConnectionError as e:
        logging.error(f"❌ Redis connection failed: {e}")
        return None
