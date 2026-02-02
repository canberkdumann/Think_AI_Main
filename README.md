# Think AI: Otonom Akıl Yürütme Motoru

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/Architecture-Multi--Agent-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**Think AI:** Veri güvenliğini esas alan otonom akıl yürütme motoru. İki farklı LLM'in birbirini sürekli denetlediği bu mimari, en doğru sonucu üretirken verilerinizi tamamen yerel depolama (local storage) alanında izole eder. Docker containerization ve Redis cache entegrasyonu ile production-ready bir altyapı sunar.

---

## Projenin Amacı

Standart dil modelleri, karmaşık mantık yürütme süreçlerinde hatalı bilgi üretmeye meyilli olabilir. Think AI, bu sorunu **BinaryMind Mimarisi** ile minimize etmeyi hedefler. Sistem, tek bir modelin çıktısını doğrudan kullanıcıya sunmak yerine, iki farklı modelin "tez-antitez" prensibiyle çalışmasını sağlar:

1.  **Analist (Qwen 2.5):** Veriyi toplar, internet kaynaklarını tarar ve bir çözüm önerisi sunar.
2.  **Eleştirmen (Gemma 2):** Sunulan çözümü mantıksal açıdan denetler, eksikleri tespit eder ve bir doğruluk payı belirler.
3.  **Sentez:** Kullanıcıya, bu iki modelin konsensüsü ile oluşturulmuş, rafine edilmiş sonuç sunulur.

Bu yaklaşım, özellikle teknik analiz, kod incelemesi ve araştırma gibi doğruluk gerektiren görevlerde daha güvenilir sonuçlar elde edilmesini sağlar.

---

## Temel Özellikler

* **Multi-Agent Orkestrasyonu:** Qwen ve Gemma modelleri asenkron olarak çalışır. Bir model üretirken diğeri denetleme mekanizması olarak görev yapar.
* **Canlı Güven Skoru:** Modeller arasındaki anlaşmazlık veya uyum seviyesi, arayüz üzerinde dinamik bir bar ile görselleştirilir. Bu sayede yapay zekanın cevabına ne kadar güvendiğini şeffaf bir şekilde görebilirsiniz.
* **Real-Time RAG:** DuckDuckGo entegrasyonu sayesinde modeller sadece eğitim verilerine bağlı kalmaz, güncel internet verilerini de analizlerine dahil eder.
* **Semantik Hafıza:** Sistem, geçmiş konuşmaları vektör tabanlı olarak saklar ve bağlamı koruyarak daha tutarlı cevaplar üretir.
* **Profesyonel Raporlama:** Analiz süreci ve sonuçları, kurumsal kullanıma uygun Markdown (.md) formatında rapor olarak dışa aktarılabilir.
* **Gizlilik Odaklı:** Ollama altyapısı sayesinde tüm veriler ve işlem gücü yerel makinenizde kalır; buluta veri gönderilmez.
* **Docker Containerization:** Tüm sistem container'larda izole çalışır. Tek komutla kurulum, cross-platform uyumluluk ve production-ready deployment.
* **Redis Cache:** Tekrar eden sorular anında yanıtlanır. %88 cache hit rate ile 35x performans artışı sağlanmıştır.
* **PII Güvenlik:** Hassas veriler (email, telefon, TC kimlik) otomatik olarak maskelenir.

<img width="1918" height="900" alt="think ai security 1" src="https://github.com/user-attachments/assets/70124c08-31f0-4ea7-be4d-0bedf8a9d6b5" />

<img width="1002" height="157" alt="think ai security 2" src="https://github.com/user-attachments/assets/61c41872-bb02-4a50-ba39-d16113113fb0" />


---

## Kullanılan Teknolojiler

Proje, modern ve ölçeklenebilir bir teknoloji yığını üzerine inşa edilmiştir:

* **Core:** Python 3.x, Asyncio (Asenkron Mimari)
* **LLM Runtime:** Ollama (Localhost)
* **Modeller:** Qwen 2.5 (Analist) & Gemma 2 (Eleştirmen)
* **AI & NLP:** PyTorch, Sentence Transformers, Scikit-learn, NumPy
* **Arayüz:** Gradio
* **Arama & RAG:** DuckDuckGo Search, Sentence Transformers, NumPy
* **Container:** Docker, Docker Compose
* **Cache:** Redis 7

---

<img width="1913" height="897" alt="think ai 1 " src="https://github.com/user-attachments/assets/54d95c40-6504-4800-b10a-3070f032e890" />
<img width="1461" height="867" alt="think ai 2" src="https://github.com/user-attachments/assets/2c4f8203-9208-4c7f-8d7a-b1fdfed9f3da" />


## Kurulum

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

### 1. Gereksinimler

* **Docker Desktop** kurulu olmalıdır
* **16 GB RAM** önerilir (minimum 8 GB)
* **15 GB boş disk alanı**

### 2. Hızlı Kurulum

**Windows:**
```powershell
git clone https://github.com/KULLANICI_ADINIZ/Think_AI_Main.git
cd Think_AI_Main
.\start.ps1
```

**Linux/Mac:**
```bash
git clone https://github.com/KULLANICI_ADINIZ/Think_AI_Main.git
cd Think_AI_Main
chmod +x start.sh
./start.sh
```

İlk çalıştırmada modeller otomatik indirilir (10-15 dakika).

### 3. Kullanım

Tarayıcınızda açın:
```
http://localhost:7860
```
