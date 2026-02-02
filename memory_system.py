from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from collections import deque

import numpy as np
from sentence_transformers import SentenceTransformer
from security_utils import SecurityFilter

class ConversationMemory:
    def __init__(self, memory_file: str = "conversation_memory.jsonl", max_history: int = 50):
        self.memory_file = Path(memory_file)
        self.max_history = max_history
        self.session_memory: deque = deque(maxlen=max_history)
        self.security = SecurityFilter()
        
        print("Memory system initializing...")
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        self._load_from_disk()
        
    def _load_from_disk(self) -> None:
        if not self.memory_file.exists():
            return
            
        try:
            with self.memory_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        self.session_memory.append(entry)
                    except:
                        continue
        except Exception as e:
            print(f"Memory load error: {e}")
    
    def add_conversation(self, user_msg: str, qwen_resp: str, gemma_resp: str, final_answer: str) -> None:
        clean_user = self.security.sanitize_text(user_msg)
        clean_qwen = self.security.sanitize_text(qwen_resp)
        clean_gemma = self.security.sanitize_text(gemma_resp)
        clean_final = self.security.sanitize_text(final_answer)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": clean_user,
            "qwen": clean_qwen,
            "gemma": clean_gemma,
            "final": clean_final,
            "hash": hashlib.md5(clean_user.encode()).hexdigest()[:8]
        }
        
        self.session_memory.append(entry)
        
        try:
            with self.memory_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Memory save error: {e}")
    
    def search_relevant_context(self, query: str, top_k: int = 3) -> str:
        if len(self.session_memory) == 0:
            return ""
        
        clean_query = self.security.sanitize_text(query)
        if self.security.check_prompt_injection(clean_query):
            return "WARNING: Potential prompt injection detected. Context retrieval blocked."

        query_embedding = self.embedder.encode([clean_query])[0]
        
        past_texts = [entry["user"] for entry in self.session_memory]
        past_embeddings = self.embedder.encode(past_texts)
        
        similarities = np.dot(past_embeddings, query_embedding) / (
            np.linalg.norm(past_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        context = "RELEVANT CONTEXT FROM HISTORY:\n\n"
        for idx in top_indices:
            if similarities[idx] > 0.3:
                entry = list(self.session_memory)[idx]
                context += f"[{entry['timestamp'][:10]}] User: {entry['user'][:100]}...\n"
                context += f"Response: {entry['final'][:200]}...\n\n"
        
        return context if len(context) > 100 else ""
    
    def get_recent_summary(self, last_n: int = 5) -> str:
        if len(self.session_memory) == 0:
            return ""
        
        recent = list(self.session_memory)[-last_n:]
        summary = "RECENT CONVERSATION SUMMARY:\n\n"
        
        for entry in recent:
            summary += f"• {entry['user'][:80]}... → {entry['final'][:120]}...\n"
        
        return summary
    
    def clear_memory(self) -> None:
        self.session_memory.clear()
        print("Session memory cleared")