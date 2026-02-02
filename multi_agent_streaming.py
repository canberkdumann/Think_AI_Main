from __future__ import annotations

import asyncio
import datetime
import json
import logging
import re
import time
import multiprocessing
import warnings
from pathlib import Path
from typing import Dict, List, TypedDict, AsyncGenerator

import httpx
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

from duckduckgo_search import DDGS
from config import DEBUG, OLLAMA_BASE_URL, MODEL_LLAMA, MODEL_GEMMA
from memory_system import ConversationMemory
from cache_manager import CacheManager

logger = logging.getLogger(__name__)
QA_MEMORY_PATH = Path("qa_memory.jsonl")
CPU_THREADS = max(1, int(multiprocessing.cpu_count() * 0.90))

MEMORY = ConversationMemory()
CACHE = CacheManager(use_redis=True)

class PanelResult(TypedDict):
    llama: str
    gemma: str
    final: str
    response_times: Dict[str, float]
    contribution_scores: Dict[str, float]
    winner: str
    cache_hit: bool

def deduplicate(text: str) -> str:
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: list[str] = []
    for p in parts:
        if p not in out:
            out.append(p)
    return "\n\n".join(out)

async def timed(name: str, coro):
    start = time.perf_counter()
    try:
        result = await coro
    except Exception as e:
        result = f"[{name}] Hata: {e}"
    elapsed = time.perf_counter() - start
    return result, elapsed

def parse_contribution_scores(decision_text: str) -> Dict[str, float]:
    scores = {"Qwen": 50.0, "Gemma": 50.0}
    
    for model in ["Qwen", "Gemma"]:
        pattern = rf'{model}.*?(\d{{1,3}})'
        match = re.search(pattern, decision_text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 0 <= val <= 100:
                    scores[model] = val
            except:
                pass
    
    total = sum(scores.values())
    if total > 0:
        for key in scores:
            scores[key] = (scores[key] / total) * 100
            
    return scores

def search_web(query: str, max_results: int = 5) -> tuple[str, List[str]]:
    print(f"\n🔎 İnternette aranıyor: '{query}'...")
    
    BAN_LIST = ["transfermarkt", "mackolik", "futbol", "soccer", "süper lig", "kupası"]
    
    clean_results = []
    try:
        raw_results = DDGS().text(query, max_results=8, region='tr-tr', backend="html")
        
        for r in raw_results:
            text_content = (r['title'] + " " + r['body']).lower()
            if any(ban in text_content for ban in BAN_LIST):
                continue
            clean_results.append(r)
            if len(clean_results) >= max_results:
                break
    except Exception:
        try:
            raw_results = DDGS().text(query, max_results=5, region='tr-tr', backend="lite")
            clean_results = raw_results
        except Exception:
            pass

    if not clean_results:
        print("❌ İlgili sonuç bulunamadı.")
        return "", []
    
    print(f"✅ {len(clean_results)} adet sonuç bulundu.")
    
    result_list = [f"[{r['title']}]\n{r['body']}" for r in clean_results]
    
    context_text = "🌐 İNTERNET ARAMA SONUÇLARI:\n"
    for i, r in enumerate(clean_results, 1):
        context_text += f"{i}. [{r['title']}]\n{r['body']}\n\n"
    
    return context_text, result_list

async def call_ollama_stream(model_name: str, messages: List[Dict[str, str]], temp: float = 0.0) -> AsyncGenerator[str, None]:
    try:
        async with httpx.AsyncClient(timeout=120.0, verify=False, trust_env=False) as client:
            async with client.stream(
                "POST",
                OLLAMA_BASE_URL,
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temp,
                        "num_ctx": 8192,
                        "num_predict": 500,
                        "num_thread": CPU_THREADS
                    }
                }
            ) as response:
                if response.status_code != 200:
                    yield f"[Hata] Sunucu: {response.status_code}"
                    return
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                chunk = data["message"]["content"]
                                if chunk:
                                    yield chunk
                        except:
                            continue
    except GeneratorExit:
        return
    except Exception as e:
        yield f"[Bağlantı Hatası: {e}]"

async def call_ollama(model_name: str, messages: List[Dict[str, str]], temp: float = 0.0) -> str:
    try:
        async with httpx.AsyncClient(timeout=120.0, verify=False, trust_env=False) as client:
            response = await client.post(
                OLLAMA_BASE_URL,
                json={
                    "model": model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temp,
                        "num_ctx": 8192,
                        "num_predict": 500,
                        "num_thread": CPU_THREADS
                    }
                }
            )
            if response.status_code != 200:
                return f"[Hata] Sunucu: {response.status_code}"
            return response.json()["message"]["content"]
    except Exception as e:
        return f"[Hata] {e}"

class LocalAgent:
    def __init__(self, name: str, model_name: str, system_prompt: str):
        self.name = name
        self.model_name = model_name
        self.system_prompt = system_prompt
    
    async def think(self, msg: str, temp_override: float = 0.0) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": msg}
        ]
        return await call_ollama(self.model_name, messages, temp=temp_override)
    
    def think_sync(self, msg: str, temp_override: float = 0.0) -> str:
        return asyncio.run(self.think(msg, temp_override))
    
    async def think_stream(self, msg: str, temp_override: float = 0.0) -> AsyncGenerator[str, None]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": msg}
        ]
        async for chunk in call_ollama_stream(self.model_name, messages, temp=temp_override):
            yield chunk

class MultiModelOrchestrator:
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        
        self.llama_chat = LocalAgent(
            "Qwen 2.5", MODEL_LLAMA,
            """Sen Qwen 2.5, dünya çapında ansiklopedik bilgiye sahip bir Türk asistanısın.

🎯 GÖREV HİYERARŞİSİ:
1. Önce GEÇMİŞ KONUŞMALARA bak (varsa)
2. Sonra İNTERNET ARAMA SONUÇLARINA bak (varsa)
3. Son olarak KENDİ DAHİLİ BİLGİNİ kullan

📋 KURALLAR:
- Arama sonuçları mantıklıysa → Kullan ve kaynak belirt
- Arama sonuçları boş/alakasız → Kendi bilgini kullan
- Geçmişte benzer soru sorulmuşsa → Tutarlı ol, çelişme
- ASLA "bilmiyorum" deme, en iyi tahmini yap
- Sayısal veriler için kesin kaynak göster

💡 UZMANLIK ALANLARIN:
- Türkiye coğrafyası (Yüzölçüm: 783.562 km²)
- Bilim, teknoloji, tarih
- Güncel olaylar (internet aramayı kullan)
- Matematik ve mantık

📝 FORMAT:
- Kısa ve net cevaplar (max 300 kelime)
- Gerekirse madde madde liste
- Kaynakları dipnotta göster"""
        )
        
        self.gemma_chat = LocalAgent(
            "Gemma 2", MODEL_GEMMA,
            """Sen Gemma 2, eleştirel düşünen bir denetçi ve yorumcusun.

🎯 GÖREV:
Qwen'in cevabını analiz et ve şunları yap:

1. DOĞRULUK KONTROLÜ:
   - Mantık hataları var mı?
   - Kaynaklar güvenilir mi?
   - Çelişki var mı?

2. EKSİKLİK TESPİTİ:
   - Neleri atlamış?
   - Hangi perspektifler eksik?
   - Daha iyi açıklama yapılabilir mi?

3. DEĞERLENDİRME:
   - Qwen'e not ver (0-100)
   - Neden bu notu verdiğini açıkla
   - Alternatif yaklaşım öner

4. SONUÇ:
   - Qwen'in cevabını onayla VEYA düzelt
   - Kendi yorumunu ekle
   - HAKLILIK PAYI: Qwen=X%, Gemma=Y%

📝 FORMAT:
- Yapıcı eleştiri (sert ama adil)
- Somut örnekler ver
- Kısa ve etkili ol (max 250 kelime)"""
        )

    async def ask_panel_async(self, msg: str) -> PanelResult:
        cache_key = msg.strip().lower()
        cached_result = CACHE.get(cache_key, "panel")
        
        if cached_result:
            print("⚡ Cache'ten getiriliyor...")
            cached_result["cache_hit"] = True
            return cached_result
        
        response_times: Dict[str, float] = {}
        
        memory_context = MEMORY.search_relevant_context(msg)
        search_context, _ = search_web(msg, max_results=5)
        
        qwen_full_prompt = ""
        if memory_context:
            qwen_full_prompt += f"{memory_context}\n{'='*60}\n\n"
        if search_context:
            qwen_full_prompt += f"{search_context}\n{'='*60}\n\n"
        qwen_full_prompt += f"KULLANICI SORUSU: {msg}\n\nYukarıdaki bilgileri kullanarak en iyi cevabı ver."
        
        llama_resp, t = await timed("Qwen 2.5", self.llama_chat.think(qwen_full_prompt))
        response_times["llama"] = t
        
        gemma_prompt = f"📌 KULLANICI SORUSU: {msg}\n\n🔵 QWEN'İN CEVABI:\n{llama_resp}\n\n{'='*60}\n"
        final_resp, t = await timed("Gemma 2", self.gemma_chat.think(gemma_prompt))
        response_times["gemma"] = t
        
        contribution_scores = parse_contribution_scores(final_resp)
        winner = "Gemma" if not contribution_scores else max(contribution_scores, key=contribution_scores.get)
        
        final_llama_text = deduplicate(llama_resp)
        sources = []
        if memory_context: sources.append("Geçmiş Konuşmalar")
        if search_context: sources.append("DuckDuckGo")
        if not sources: sources.append("Qwen Dahili Hafıza")
        final_llama_text += f"\n\n🔍 [Kaynaklar: {', '.join(sources)}]"
        
        MEMORY.add_conversation(user_msg=msg, qwen_resp=llama_resp, gemma_resp=final_resp, final_answer=deduplicate(final_resp))
        
        result = {
            "llama": final_llama_text,
            "gemma": deduplicate(final_resp),
            "final": deduplicate(final_resp),
            "response_times": response_times,
            "contribution_scores": contribution_scores,
            "winner": winner,
            "cache_hit": False
        }
        
        CACHE.set(cache_key, "panel", result, ttl=3600)
        
        return result
    
    async def compare_async(self, topic: str, text1: str, text2: str) -> PanelResult:
        response_times: Dict[str, float] = {}
        
        qwen_prompt = f"Sen Qwen, 1. METNİ savunuyorsun.\n\nKONU: {topic}\n\n1. METİN (SENİN):\n{text1}\n\n2. METİN (RAKİP):\n{text2}\n\nGÖREV: 1. metnin neden daha iyi olduğunu savun."
        llama_resp, t = await timed("Qwen", self.llama_chat.think(qwen_prompt, temp_override=0.3))
        response_times["llama"] = t
        
        gemma_prompt = f"Sen Gemma, 2. METNİ savunuyorsun ama aynı zamanda HAKEMsin.\n\nKONU: {topic}\n\n1. METİN:\n{text1}\n\n2. METİN (SENİN):\n{text2}\n\nQWEN'İN SAVUNMASI:\n{llama_resp}\n\nGÖREV: 2. metnin güçlü yanlarını savun ve HAKLILIK PAYI ver."
        final_resp, t = await timed("Gemma", self.gemma_chat.think(gemma_prompt, temp_override=0.3))
        response_times["gemma"] = t
        
        contribution_scores = parse_contribution_scores(final_resp)
        winner = "Qwen" if contribution_scores.get("Qwen", 0) > contribution_scores.get("Gemma", 0) else "Gemma"
        
        return {
            "llama": deduplicate(llama_resp),
            "gemma": deduplicate(final_resp),
            "final": deduplicate(final_resp),
            "response_times": response_times,
            "contribution_scores": contribution_scores,
            "winner": winner,
            "cache_hit": False
        }