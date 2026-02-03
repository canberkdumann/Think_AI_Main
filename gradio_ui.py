import gradio as gr
from multi_agent_streaming import LocalAgent, MEMORY, search_web, parse_contribution_scores
from config import MODEL_LLAMA, MODEL_GEMMA
import json
from datetime import datetime
import os
import asyncio

STOP_EVENT = asyncio.Event()
PAUSE_EVENT = asyncio.Event()

conversation_history = []
current_conversation = []

UI_TEXTS = {
    "tr": {
        "page_title": "Think AI",
        "sub_title": "Autonomous Reasoning Engine",
        "tech_info": "Powered by <b>BinaryMind Architecture</b><br>Qwen 2.5 & Gemma 2",
        "history_header": "### 📂 Proje Hafızası",
        "history_label": "Geçmiş Analizler",
        "load_btn": "📂 Yükle",
        "settings_header": "### ⚙️ BinaryMind Ayarları",
        "rounds_label": "Derinlik (Tur Sayısı)",
        "lang_label": "Arayüz & Çıktı Dili / Language",
        "export_btn": "📄 Profesyonel Rapor İndir (.md)",
        "status_label": "Sistem Durumu",
        "input_label": "Think AI Ne Üzerinde Çalışsın?",
        "input_placeholder": "Örn: Microservice mimarisinde JWT kullanımı mantıklı mı? Avantaj ve dezavantajları neler?",
        "think_btn": "🧠 Düşünceyi Başlat",
        "stop_btn": "⏸️ Duraklat",
        "continue_btn": "▶️ Devam Et",
        "reset_btn": "🗑️ Sıfırla",
        "output_label": "Sentez Raporu",
        "warn_input": "⚠️ Lütfen bir konu girin",
        "status_processing": "⏳ Tur {} işleniyor...",
        "status_searching": "🔍 İnternet araması yapılıyor...",
        "status_writing_qwen": "🤖 Qwen yazıyor...",
        "status_writing_gemma": "🤖 Gemma yazıyor...",
        "status_done_round": "✓ Tur {} bitti",
        "status_complete": "✨ Analiz tamamlandı.",
        "status_ready": "✓ Hazır",
        "status_paused": "⏸️ Duraklatıldı. Devam etmek için butona basın.",
        "status_stopped": "⛔ İşlem iptal edildi.",
        "err": "❌ Hata",
        "bar_qwen": "Qwen 2.5 (Analist)",
        "bar_center": "Güven Dengesi",
        "bar_gemma": "Gemma 2 (Eleştirmen)",
        "topic_header": "📌 Konu:",
        "lang_header": "🌍 Dil:",
        "rounds_header": "🔄 Derinlik:",
        "round_title": "TUR",
        "internet_check": "🌐 İnternet Kontrolü..."
    },
    "en": {
        "page_title": "Think AI",
        "sub_title": "Autonomous Reasoning Engine",
        "tech_info": "Powered by <b>BinaryMind Architecture</b><br>Qwen 2.5 & Gemma 2",
        "history_header": "### 📂 Project Memory",
        "history_label": "Past Analyses",
        "load_btn": "📂 Load",
        "settings_header": "### ⚙️ BinaryMind Settings",
        "rounds_label": "Depth (Rounds)",
        "lang_label": "Interface & Output Language",
        "export_btn": "📄 Download Professional Report (.md)",
        "status_label": "System Status",
        "input_label": "What should Think AI work on?",
        "input_placeholder": "Ex: Is using JWT in microservice architecture logical? What are the pros and cons?",
        "think_btn": "🧠 Start Reasoning",
        "stop_btn": "⏸️ Pause",
        "continue_btn": "▶️ Continue",
        "reset_btn": "🗑️ Reset",
        "output_label": "Synthesis Report",
        "warn_input": "⚠️ Please enter a topic",
        "status_processing": "⏳ Processing Round {}...",
        "status_searching": "🔍 Searching the web...",
        "status_writing_qwen": "🤖 Qwen is writing...",
        "status_writing_gemma": "🤖 Gemma is writing...",
        "status_done_round": "✓ Round {} finished",
        "status_complete": "✨ Analysis complete.",
        "status_ready": "✓ Ready",
        "status_paused": "⏸️ Paused. Press continue to resume.",
        "status_stopped": "⛔ Process cancelled.",
        "err": "❌ Error",
        "bar_qwen": "Qwen 2.5 (Analyst)",
        "bar_center": "Confidence Balance",
        "bar_gemma": "Gemma 2 (Critic)",
        "topic_header": "📌 Topic:",
        "lang_header": "🌍 Lang:",
        "rounds_header": "🔄 Rounds:",
        "round_title": "ROUND",
        "internet_check": "🌐 Internet Check..."
    }
}

LANGUAGES_PROMPT = {
    "tr": "Türkçe konuş ve Türkçe cevap ver.",
    "en": "Speak and respond in English."
}

def get_confidence_html(qwen_score, gemma_score, lang="tr"):
    t = UI_TEXTS[lang]
    return f"""
    <div style="margin-bottom: 10px; font-family: sans-serif;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-weight: bold; font-size: 0.9em;">
            <span style="color: #3b82f6;">{t['bar_qwen']}</span>
            <span style="color: #666; font-size: 0.8em;">{t['bar_center']}</span>
            <span style="color: #ef4444;">{t['bar_gemma']}</span>
        </div>
        <div style="width: 100%; background-color: #e5e7eb; border-radius: 999px; height: 16px; position: relative; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
            <div style="width: {qwen_score}%; background: linear-gradient(90deg, #2563eb 0%, #60a5fa 100%); height: 100%; position: absolute; left: 0; top: 0; transition: width 0.5s ease;"></div>
            <div style="width: {gemma_score}%; background: linear-gradient(90deg, #f87171 0%, #dc2626 100%); height: 100%; position: absolute; right: 0; top: 0; transition: width 0.5s ease;"></div>
            <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 2px; background: rgba(255,255,255,0.8); z-index: 10;"></div>
        </div>
        <div style="text-align: center; font-size: 0.8em; color: #666; margin-top: 2px;">
            %{qwen_score:.1f} vs %{gemma_score:.1f}
        </div>
    </div>
    """

async def check_pause():
    if not PAUSE_EVENT.is_set():
        await PAUSE_EVENT.wait()

async def start_thinking_stream(question, rounds, language):
    global current_conversation, conversation_history
    
    STOP_EVENT.clear()
    PAUSE_EVENT.set() 
    
    t = UI_TEXTS[language]
    initial_bar = get_confidence_html(50, 50, language)
    current_conversation = []
    
    if not question or not question.strip():
        yield t["warn_input"], gr.update(), "", initial_bar
        return
    
    lang_instruction = LANGUAGES_PROMPT.get(language, LANGUAGES_PROMPT["tr"])
    
    try:
        qwen = LocalAgent(
            "Qwen", MODEL_LLAMA,
            f"Sen akıllı bir analiz asistanısın.\nİlk 3 turda farklı perspektifler sun.\nSonra sentez yap.\nKısa ve net ol.\n{lang_instruction}"
        )
        gemma = LocalAgent(
            "Gemma", MODEL_GEMMA,
            f"Sen eleştirel düşünce asistanısın.\nAlternatif görüşler sun.\nQwen'in görüşüne ne kadar katıldığını (Haklılık Payı: %X) belirt.\nKısa ve net ol.\n{lang_instruction}"
        )
        
        output = f"{t['topic_header']} {question}\n"
        output += f"{t['lang_header']} {language.upper()} | {t['rounds_header']} {rounds}\n"
        output += f"{'─'*40}\n\n"
        
        current_conversation.append({"header": True, "text": output})
        max_rounds = int(rounds) if rounds else 3
        current_context = question
        gemma_last = ""
        current_scores = {"Qwen": 50.0, "Gemma": 50.0}
        
        last_qwen_resp = ""
        last_gemma_resp = ""
        
        for round_count in range(1, max_rounds + 1):
            if STOP_EVENT.is_set(): break
            await check_pause() 
            
            mode_text = "Perspektif Analizi" if language == "tr" and round_count <= 3 else \
                        "Derin Sentez" if language == "tr" else \
                        "Perspective Analysis" if round_count <= 3 else "Deep Synthesis"
                        
            round_header = f"\n📍 {t['round_title']} {round_count}/{max_rounds} - {mode_text}\n\n"
            output += round_header
            bar_html = get_confidence_html(current_scores["Qwen"], current_scores["Gemma"], language)
            yield output, gr.update(), t["status_processing"].format(round_count), bar_html
            
            search_context = ""
            if round_count % 3 == 0:
                output += f"{t['internet_check']}\n\n"
                yield output, gr.update(), t["status_searching"], bar_html
                try:
                    search_context, _ = search_web(current_context, max_results=3)
                except:
                    pass
            
            if STOP_EVENT.is_set(): break
            await check_pause()
            
            if round_count == 1:
                qwen_prompt = f"Soru: {question}\n\nBu konuyu analiz et."
            else:
                qwen_prompt = f"Önceki: {gemma_last}\n\nEleştir ve sentezle."
            if search_context: qwen_prompt += f"\n\nBilgi:\n{search_context[:500]}"
            
            output += "🤖 Qwen:\n"
            qwen_response = ""
            async for chunk in qwen.think_stream(qwen_prompt, temp_override=0.8):
                if STOP_EVENT.is_set(): break
                await check_pause()
                if chunk:
                    qwen_response += chunk
                    yield output + qwen_response + " ▌", gr.update(), t["status_writing_qwen"], bar_html
            
            last_qwen_resp = qwen_response
            output += qwen_response + "\n\n"
            
            if language == "en":
                gemma_prompt = f"Opinion: {qwen_response}\n\nProvide an alternative perspective and explicitly state Qwen's Accuracy/Confidence Score (as %) within the text."
            else:
                gemma_prompt = f"Görüş: {qwen_response}\n\nAlternatif bakış sun ve Qwen'in bu turdaki doğruluk/haklılık payını (% olarak) metin içinde geçir."

            output += "🤖 Gemma:\n"
            gemma_response = ""
            async for chunk in gemma.think_stream(gemma_prompt, temp_override=0.8):
                if STOP_EVENT.is_set(): break
                await check_pause()
                if chunk:
                    gemma_response += chunk
                    yield output + gemma_response + " ▌", gr.update(), t["status_writing_gemma"], bar_html
            
            last_gemma_resp = gemma_response
            gemma_last = gemma_response
            output += gemma_response + "\n\n"
            output += f"{'─'*40}\n"
            
            new_scores = parse_contribution_scores(gemma_response)
            if new_scores["Qwen"] != 50.0 or new_scores["Gemma"] != 50.0:
                current_scores = new_scores
            bar_html = get_confidence_html(current_scores["Qwen"], current_scores["Gemma"], language)
            yield output, gr.update(), t["status_done_round"].format(round_count), bar_html
            
            current_conversation.append({
                "round": round_count,
                "mode": mode_text,
                "qwen": qwen_response,
                "gemma": gemma_response,
                "scores": current_scores,
                "timestamp": datetime.now().isoformat()
            })
            current_context = f"{qwen_response[-200:]} {gemma_response[-200:]}"
        
        if STOP_EVENT.is_set():
             output += f"\n{t['status_stopped']}\n"
        else:
             output += f"\n{t['status_complete']}\n"
             MEMORY.add_conversation(
                 user_msg=question,
                 qwen_resp=last_qwen_resp,
                 gemma_resp=last_gemma_resp,
                 final_answer=last_gemma_resp
             )
        
        conversation_history.append({
            "question": question,
            "rounds": max_rounds,
            "language": language,
            "conversation": current_conversation,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        if len(conversation_history) > 50: conversation_history.pop(0)
        
        yield output, gr.update(choices=_get_history_list(), value=None), t["status_ready"], bar_html
        
    except GeneratorExit:
        pass
    except Exception as e:
        output += f"\n{t['err']}: {str(e)}\n"
        yield output, gr.update(), t["err"], get_confidence_html(50, 50, language)

def pause_action(language):
    PAUSE_EVENT.clear()
    t = UI_TEXTS[language]
    return gr.update(visible=False), gr.update(visible=True), t["status_paused"]

def continue_action(language):
    PAUSE_EVENT.set()
    t = UI_TEXTS[language]
    return gr.update(visible=False), gr.update(visible=True), t["status_processing"].format("...")

def stop_action(language):
    STOP_EVENT.set()
    PAUSE_EVENT.set()
    reset_interface(language)

def reset_interface(language):
    STOP_EVENT.set()
    PAUSE_EVENT.set()
    t = UI_TEXTS[language]
    return (
        "", "", t["status_ready"], get_confidence_html(50, 50, language),
        gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)
    )

def _get_history_list():
    if not conversation_history: return []
    history_list = []
    for conv in reversed(conversation_history):
        q_text = conv.get("question", "???")
        preview = q_text[:30] + "..." if len(q_text) > 30 else q_text
        history_list.append(f"[{conv.get('timestamp','')}] {preview}")
    return history_list

def load_history(selection):
    global conversation_history
    if not selection: return "", "⚠️", get_confidence_html(50, 50)
    try:
        idx = len(conversation_history) - 1 - _get_history_list().index(selection)
        conv = conversation_history[idx]
        output = ""
        for item in conv["conversation"]:
            if "header" in item: output += item["text"]
            elif "round" in item:
                output += f"\n📍 TUR {item['round']} - {item.get('mode','')}\n\n🤖 Qwen:\n{item['qwen']}\n\n🤖 Gemma:\n{item['gemma']}\n\n{'─'*40}\n"
        last_item = conv["conversation"][-1]
        last_scores = last_item.get("scores", {"Qwen":50, "Gemma":50}) if "scores" in last_item else {"Qwen":50, "Gemma":50}
        saved_lang = conv.get("language", "tr")
        return output, "✓", get_confidence_html(last_scores["Qwen"], last_scores["Gemma"], saved_lang)
    except: return "", "❌", get_confidence_html(50, 50)

def export_current_conversation(format_type):
    if not current_conversation: return None
    os.makedirs("exports", exist_ok=True)
    filename = f"ThinkAI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    filepath = os.path.join("exports", filename)
    content = f"# 🧠 Think AI - Sentez Raporu\n**Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n---\n\n"
    for item in current_conversation:
        if "header" in item: content += f"### {item['text']}\n"
        elif "round" in item:
            scores = item.get('scores', {'Qwen':50, 'Gemma':50})
            content += f"## 📍 TUR {item['round']}\n### 🔵 Qwen\n{item['qwen']}\n\n### 🔴 Gemma\n{item['gemma']}\n> Dengesi: Qwen %{scores['Qwen']:.1f} - Gemma %{scores['Gemma']:.1f}\n---\n"
    with open(filepath, "w", encoding="utf-8") as f: f.write(content)
    return filepath

def update_interface_language(lang):
    t = UI_TEXTS[lang]
    bar = get_confidence_html(50, 50, lang)
    return (
        gr.update(value=t["history_header"]), gr.update(label=t["history_label"]),
        gr.update(value=t["load_btn"]), gr.update(value=t["settings_header"]),
        gr.update(label=t["rounds_label"]), gr.update(value=t["export_btn"]),
        gr.update(label=t["status_label"]), bar, 
        gr.update(label=t["input_label"], placeholder=t["input_placeholder"]),
        gr.update(value=t["think_btn"]), gr.update(value=t["stop_btn"]),
        gr.update(value=t["continue_btn"]), gr.update(value=t["reset_btn"]),
        gr.update(label=t["output_label"])
    )

custom_css = """
.gradio-container { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important; background-color: #f9f9f9 !important; }
#output-box textarea { 
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important; 
    font-size: 16px !important; 
    line-height: 1.6 !important;
    background-color: #ffffff !important; 
    color: #1f2937 !important; 
    padding: 15px !important; 
    border-radius: 8px !important; 
}
.primary-btn { background: #2d3748 !important; color: white !important; border: none !important; }
.stop-btn { background: #e53e3e !important; color: white !important; }
.continue-btn { background: #38a169 !important; color: white !important; }
.reset-btn { background: #718096 !important; color: white !important; }
.sidebar { background: #ffffff !important; padding: 15px !important; border-right: 1px solid #eee !important; border-radius: 8px !important; }
"""

with gr.Blocks(css=custom_css, title="Think AI") as demo:
    with gr.Row():
        with gr.Column(scale=1): gr.Markdown("# Think AI\n<h3 style='color: gray; margin-top: 0;'>Autonomous Reasoning Engine</h3>")
        with gr.Column(scale=1): gr.Markdown("<div style='text-align: right; color: #999;'>Powered by <b>BinaryMind</b></div>")
    gr.Markdown("---")

    with gr.Row():
        with gr.Column(scale=1, elem_classes="sidebar", min_width=250):
            history_header = gr.Markdown(UI_TEXTS["tr"]["history_header"])
            history_dropdown = gr.Dropdown(label=UI_TEXTS["tr"]["history_label"], choices=[])
            load_btn = gr.Button(UI_TEXTS["tr"]["load_btn"], size="sm")
            gr.Markdown("---")
            settings_header = gr.Markdown(UI_TEXTS["tr"]["settings_header"])
            think_rounds = gr.Number(label=UI_TEXTS["tr"]["rounds_label"], value=3, minimum=1, maximum=10)
            think_language = gr.Dropdown(label=UI_TEXTS["tr"]["lang_label"], choices=[("🇹🇷 Türkçe", "tr"), ("🇬🇧 English", "en")], value="tr")
            gr.Markdown("---")
            export_btn = gr.Button(UI_TEXTS["tr"]["export_btn"], size="sm")
            export_file = gr.File(visible=True, label="İndirilen Rapor")
            status_text = gr.Textbox(label=UI_TEXTS["tr"]["status_label"], interactive=False, max_lines=1)

        with gr.Column(scale=4):
            confidence_display = gr.HTML(value=get_confidence_html(50, 50, "tr"))
            think_question = gr.Textbox(label=UI_TEXTS["tr"]["input_label"], placeholder=UI_TEXTS["tr"]["input_placeholder"], lines=3)
            
            with gr.Row():
                think_btn = gr.Button(UI_TEXTS["tr"]["think_btn"], variant="primary", scale=2, elem_classes="primary-btn")
                stop_btn = gr.Button(UI_TEXTS["tr"]["stop_btn"], variant="stop", scale=1, elem_classes="stop-btn", visible=False)
                continue_btn = gr.Button(UI_TEXTS["tr"]["continue_btn"], variant="primary", scale=1, elem_classes="continue-btn", visible=False)
                reset_btn = gr.Button(UI_TEXTS["tr"]["reset_btn"], variant="secondary", scale=1, elem_classes="reset-btn")
            
            think_output = gr.Textbox(label=UI_TEXTS["tr"]["output_label"], elem_id="output-box", lines=20, max_lines=40)

    think_btn.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)),
        outputs=[think_btn, stop_btn, continue_btn]
    ).then(
        fn=start_thinking_stream, 
        inputs=[think_question, think_rounds, think_language], 
        outputs=[think_output, history_dropdown, status_text, confidence_display]
    ).then(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)),
        outputs=[think_btn, stop_btn, continue_btn]
    )
    
    stop_btn.click(fn=pause_action, inputs=[think_language], outputs=[stop_btn, continue_btn, status_text])
    continue_btn.click(fn=continue_action, inputs=[think_language], outputs=[continue_btn, stop_btn, status_text])
    reset_btn.click(fn=reset_interface, inputs=[think_language], outputs=[think_question, think_output, status_text, confidence_display, think_btn, stop_btn, continue_btn])
    
    think_language.change(fn=update_interface_language, inputs=[think_language], outputs=[history_header, history_dropdown, load_btn, settings_header, think_rounds, export_btn, status_text, confidence_display, think_question, think_btn, stop_btn, continue_btn, reset_btn, think_output])
    load_btn.click(load_history, inputs=[history_dropdown], outputs=[think_output, status_text, confidence_display])
    export_btn.click(export_current_conversation, inputs=[gr.State("MD")], outputs=[export_file])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
