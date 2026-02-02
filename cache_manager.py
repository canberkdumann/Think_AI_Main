from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import redis

class CacheManager:
    def __init__(self, use_redis: bool = True, redis_host: str = "redis", redis_port: int = 6379):
        self.use_redis = use_redis
        
        if use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                print("✅ Redis cache connected")
            except:
                print("⚠️ Redis unavailable, using file cache")
                self.use_redis = False
                self._init_file_cache()
        else:
            self._init_file_cache()
    
    def _init_file_cache(self):
        self.cache_dir = Path("cache_data")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "query_cache.json"
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.file_cache = json.load(f)
            except:
                self.file_cache = {}
        else:
            self.file_cache = {}
    
    def _generate_key(self, query: str, model_name: str) -> str:
        combined = f"{model_name}:{query.strip().lower()}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, query: str, model_name: str) -> Optional[Dict[str, Any]]:
        key = self._generate_key(query, model_name)
        
        if self.use_redis:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    data = json.loads(cached)
                    if time.time() - data["timestamp"] < data["ttl"]:
                        return data["response"]
                    else:
                        self.redis_client.delete(key)
                        return None
            except:
                return None
        else:
            if key in self.file_cache:
                data = self.file_cache[key]
                if time.time() - data["timestamp"] < data["ttl"]:
                    return data["response"]
                else:
                    del self.file_cache[key]
                    self._save_file_cache()
                    return None
        
        return None
    
    def set(self, query: str, model_name: str, response: Dict[str, Any], ttl: int = 3600):
        key = self._generate_key(query, model_name)
        
        cache_data = {
            "response": response,
            "timestamp": time.time(),
            "ttl": ttl
        }
        
        if self.use_redis:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(cache_data)
                )
            except:
                pass
        else:
            self.file_cache[key] = cache_data
            self._save_file_cache()
    
    def _save_file_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.file_cache, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def clear(self):
        if self.use_redis:
            try:
                self.redis_client.flushdb()
            except:
                pass
        else:
            self.file_cache = {}
            self._save_file_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        if self.use_redis:
            try:
                info = self.redis_client.info()
                return {
                    "type": "redis",
                    "total_keys": self.redis_client.dbsize(),
                    "memory_used": info.get("used_memory_human", "N/A"),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0)
                }
            except:
                return {"type": "redis", "status": "error"}
        else:
            valid_keys = 0
            expired_keys = 0
            current_time = time.time()
            
            for data in self.file_cache.values():
                if current_time - data["timestamp"] < data["ttl"]:
                    valid_keys += 1
                else:
                    expired_keys += 1
            
            return {
                "type": "file",
                "total_keys": len(self.file_cache),
                "valid_keys": valid_keys,
                "expired_keys": expired_keys
            }