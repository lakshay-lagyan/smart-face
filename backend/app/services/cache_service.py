import logging
import json
import redis
from typing import Optional, Any
from functools import wraps

logger = logging.getLogger(__name__)

class CacheService:
    
    def __init__(self):
        self.redis_client = None
        self.fallback_cache = {}
        self.is_available = False
        self.default_ttl = 3600  # 1 hour
        
    def initialize(self, redis_url: Optional[str] = None):
        """Initialize Redis connection"""
        if redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.is_available = True
                logger.info("[Cache] Redis connected successfully")
                
            except Exception as e:
                logger.warning(f"[Cache] Redis unavailable: {e}, using fallback")
                self.is_available = False
        else:
            logger.info("[Cache] Redis not configured, using fallback")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.is_available and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self.fallback_cache.get(key)
                
        except Exception as e:
            logger.error(f"[Cache] Get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value)
            
            if self.is_available and self.redis_client:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.fallback_cache[key] = serialized
                
            return True
            
        except Exception as e:
            logger.error(f"[Cache] Set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.is_available and self.redis_client:
                self.redis_client.delete(key)
            else:
                self.fallback_cache.pop(key, None)
                
            return True
            
        except Exception as e:
            logger.error(f"[Cache] Delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.is_available and self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                return key in self.fallback_cache
                
        except Exception as e:
            logger.error(f"[Cache] Exists error for key {key}: {e}")
            return False
    
    def clear(self, pattern: Optional[str] = None) -> bool:
        """Clear cache (all keys or matching pattern)"""
        try:
            if self.is_available and self.redis_client:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
            else:
                if pattern:
                    keys_to_delete = [k for k in self.fallback_cache.keys() if pattern in k]
                    for k in keys_to_delete:
                        del self.fallback_cache[k]
                else:
                    self.fallback_cache.clear()
                    
            logger.info(f"[Cache] Cleared cache (pattern: {pattern})")
            return True
            
        except Exception as e:
            logger.error(f"[Cache] Clear error: {e}")
            return False
    
    def ping(self) -> bool:
        """Check if cache is responsive"""
        try:
            if self.is_available and self.redis_client:
                return self.redis_client.ping()
            return True  # Fallback is always available
            
        except Exception as e:
            logger.error(f"[Cache] Ping error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        try:
            if self.is_available and self.redis_client:
                return self.redis_client.incrby(key, amount)
            else:
                current = self.fallback_cache.get(key, '0')
                new_value = int(current) + amount
                self.fallback_cache[key] = str(new_value)
                return new_value
                
        except Exception as e:
            logger.error(f"[Cache] Increment error for key {key}: {e}")
            return None
    
    def get_many(self, keys: list) -> dict:
        """Get multiple values at once"""
        try:
            results = {}
            
            if self.is_available and self.redis_client:
                values = self.redis_client.mget(keys)
                for key, value in zip(keys, values):
                    if value:
                        results[key] = json.loads(value)
            else:
                for key in keys:
                    if key in self.fallback_cache:
                        results[key] = json.loads(self.fallback_cache[key])
                        
            return results
            
        except Exception as e:
            logger.error(f"[Cache] Get many error: {e}")
            return {}
    
    def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values at once"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.is_available and self.redis_client:
                pipe = self.redis_client.pipeline()
                for key, value in mapping.items():
                    serialized = json.dumps(value)
                    pipe.setex(key, ttl, serialized)
                pipe.execute()
            else:
                for key, value in mapping.items():
                    self.fallback_cache[key] = json.dumps(value)
                    
            return True
            
        except Exception as e:
            logger.error(f"[Cache] Set many error: {e}")
            return False


# Decorator for caching function results
def cache_result(ttl: int = 3600, key_prefix: str = ''):
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = cache_service.get(cache_key)
            if cached is not None:
                logger.debug(f"[Cache] Hit for {cache_key}")
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_service.set(cache_key, result, ttl)
            logger.debug(f"[Cache] Stored {cache_key}")
            
            return result
            
        return wrapper
    return decorator


# Global instance
cache_service = CacheService()
