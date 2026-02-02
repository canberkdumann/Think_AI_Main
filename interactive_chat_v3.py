from __future__ import annotations

import asyncio
import logging
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich.live import Live

from config import DEBUG
from multi_agent_streaming import MultiModelOrchestrator, MEMORY
from ultimate_think import UltimateThink

console = Console()

def setup_logging() -> None:
    logging.basicConfig(level=logging.ERROR)

async def chat_loop() -> None:
    orchestrator = MultiModelOrchestrator()

    help_text = """🧠 ULTIMATE AI THINK - Qwen 7B + Gemma 9B

DÜŞÜNCE MOTORU:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 TUR 1-3   → Eleştirel mod (Farklı perspektifler)
💡 TUR 4-10  → Derinleşme (Yaratıcı sentez)
💡 TUR 10+   → Felsefi boyut
🔍 Her 3 tur → İnternet araması
⚡ İstediğin kadar tur belirle!

KOMUTLAR:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/think     → Derin düşünce başlat 🧠
/memory    → Hafıza özeti
/clear     → Hafıza temizle
q          → Çıkış

Normal yaz → Tek seferlik soru-cevap"""

    console.print(Panel(help_text, title="🎯 ULTIMATE THINK AI", border_style="magenta"))

    while True:
        try:
            console.print("\n[bold green]Sen:[/bold green] ", end="")
            user_input = input("")
        except:
            break

        if not user_input:
            continue
        if user_input.lower() in {"q", "quit", "çık"}:
            break
        
        if user_input.strip() == "/memory":
            summary = MEMORY.get_recent_summary(last_n=5)
            if summary:
                console.print(Panel(summary, title="🧠 HAFIZA ÖZETİ", border_style="yellow"))
            else:
                console.print("[dim]Henüz hafızada bir şey yok.[/dim]")
            continue
        
        if user_input.strip() == "/clear":
            MEMORY.clear_memory()
            console.print("[green]✅ Hafıza temizlendi[/green]")
            continue
        
        if user_input.strip() == "/think":
            console.print("\n[bold magenta]🧠 ULTIMATE THINK MODE[/bold magenta]\n")
            
            console.print("[bold yellow]Kaç tur düşünsünler?[/bold yellow]")
            console.print("[dim](Sayı gir = O kadar tur | Enter = Sonsuz)[/dim]")
            rounds_input = input("Tur sayısı: ").strip()
            
            max_rounds = 0
            if rounds_input.isdigit():
                max_rounds = int(rounds_input)
                if max_rounds < 1:
                    console.print("[red]En az 1 tur olmalı![/red]")
                    continue
            
            console.print()
            question = input("💭 Konu/Soru: ").strip()
            if not question:
                console.print("[red]Konu boş olamaz![/red]")
                continue
            
            think = UltimateThink()
            await think.start_ultimate_think(question, max_rounds)
            continue

        else:
            memory_context = MEMORY.search_relevant_context(user_input)
            
            from multi_agent_streaming import search_web
            search_context, result_list = search_web(user_input, max_results=5)
            
            if result_list:
                for i, result in enumerate(result_list, 1):
                    console.print(f"[dim]📄 Kaynak {i} yüklendi...[/dim]")
                    await asyncio.sleep(0.2)
            
            qwen_full_prompt = ""
            if memory_context:
                qwen_full_prompt += f"{memory_context}\n{'='*60}\n\n"
            if search_context:
                qwen_full_prompt += f"{search_context}\n{'='*60}\n\n"
            
            qwen_full_prompt += f"KULLANICI SORUSU: {user_input}\n\n"
            
            if search_context:
                qwen_full_prompt += "⚠️ UYARI: Yukarıda internet arama sonuçları var! MUTLAKA ONLARI KULLAN ve soruya NET CEVAP VER (sayı/tarih belirt)!\n\n"
            else:
                qwen_full_prompt += "İnternet araması yok, kendi bilginle cevapla.\n\n"
            
            qwen_full_prompt += "Cevap ver:"
            
            console.print("\n[bold blue]🔵 Qwen 2.5 düşünüyor...[/bold blue]\n")
            qwen_response = ""
            qwen_start = time.time()
            
            qwen_text = Text()
            with Live(qwen_text, console=console, refresh_per_second=5) as live:
                try:
                    async for chunk in orchestrator.llama_chat.think_stream(qwen_full_prompt):
                        if chunk and len(chunk.strip()) > 0:
                            qwen_response += chunk
                            qwen_text.append(chunk, style="blue")
                            try:
                                live.update(qwen_text)
                            except:
                                pass
                except Exception as e:
                    console.print(f"[dim red]Hata: {e}[/dim red]")
            
            qwen_time = time.time() - qwen_start
            console.print(qwen_text)
            console.print()
            
            sources = []
            if memory_context: sources.append("Hafıza")
            if search_context: sources.append("Web")
            if not sources: sources.append("Dahili")
            console.print(f"[dim]🔍 [{', '.join(sources)}] ({qwen_time:.1f}s)[/dim]\n")
            
            gemma_prompt = f"SORU: {user_input}\n\nQWEN: {qwen_response}\n\nGÖREV: Değerlendir ve HAKLILIK PAYI ver (Qwen=X%, Gemma=Y%)"
            
            console.print("[bold red]🔴 Gemma 2 düşünüyor...[/bold red]\n")
            gemma_response = ""
            gemma_start = time.time()
            
            gemma_text = Text()
            with Live(gemma_text, console=console, refresh_per_second=5) as live:
                try:
                    async for chunk in orchestrator.gemma_chat.think_stream(gemma_prompt):
                        if chunk and len(chunk.strip()) > 0:
                            gemma_response += chunk
                            gemma_text.append(chunk, style="red")
                            try:
                                live.update(gemma_text)
                            except:
                                pass
                except Exception as e:
                    console.print(f"[dim red]Hata: {e}[/dim red]")
            
            gemma_time = time.time() - gemma_start
            console.print(gemma_text)
            console.print()
            console.print(f"[dim]({gemma_time:.1f}s)[/dim]\n")
            
            from multi_agent_streaming import parse_contribution_scores
            contribution_scores = parse_contribution_scores(gemma_response)
            winner = "Gemma" if not contribution_scores else max(contribution_scores, key=contribution_scores.get)
            
            console.print(f"🏆 Kazanan: [bold cyan]{winner.upper()}[/bold cyan]")
            console.print(f"⏱️  Qwen={qwen_time:.1f}s | Gemma={gemma_time:.1f}s")
            
            if contribution_scores:
                console.print("\n📊 Başarı Grafiği:")
                with Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(complete_style="green", finished_style="green"),
                    TextColumn("{task.percentage:>3.0f}%"),
                    console=console,
                ) as progress:
                    q_score = contribution_scores.get("Qwen", 50.0)
                    g_score = contribution_scores.get("Gemma", 50.0)
                    progress.add_task("  QWEN ", total=100, completed=q_score)
                    progress.add_task("  GEMMA", total=100, completed=g_score)
            
            MEMORY.add_conversation(
                user_msg=user_input,
                qwen_resp=qwen_response,
                gemma_resp=gemma_response,
                final_answer=gemma_response
            )
            
            console.print("-" * 60)

def main() -> None:
    setup_logging()
    asyncio.run(chat_loop())

if __name__ == "__main__":
    main()