# Think AI: Autonomous Reasoning Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/Architecture-Multi--Agent-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**Think AI:** A privacy-first autonomous reasoning engine. This architecture employs two distinct LLMs that continuously cross-examine each other to produce the most accurate results, ensuring your data remains entirely isolated in local storage. It delivers a production-ready infrastructure with full Docker containerization and Redis cache integration.

---

## Project Purpose

Standard language models can be prone to hallucinations during complex reasoning processes. Think AI aims to minimize this issue through its **BinaryMind Architecture**. Instead of presenting a single model's output directly to the user, the system operates on a "thesis-antithesis" principle:

1.  **The Analyst (Qwen 2.5):** Gathers data, scans web resources, and proposes an initial solution.
2.  **The Critic (Gemma 2):** Audits the proposed solution for logical consistency, identifies gaps, and assigns a truth probability score.
3.  **Synthesis:** A refined conclusion is presented to the user, formed by the consensus of these two models.

This approach ensures more reliable outcomes, especially in tasks requiring high accuracy such as technical analysis, code review, and deep research.

---

## Key Features

* **Multi-Agent Orchestration:** Qwen and Gemma models operate asynchronously. While one generates content, the other acts as an oversight mechanism.
* **Live Confidence Score:** The level of agreement or conflict between models is visualized via a dynamic bar on the interface, providing transparency on how much the AI trusts its own answer.
* **Real-Time RAG:** Thanks to DuckDuckGo integration, models rely not only on training data but also analyze current internet data.
* **Semantic Memory:** The system stores past conversations using vector embeddings, maintaining context for more consistent responses.
* **Professional Reporting:** Analysis processes and results can be exported as Markdown (.md) reports suitable for corporate use.
* **Privacy-First:** Powered by the Ollama infrastructure, all data and processing power remain on your local machine; no data is sent to the cloud.
* **Docker Containerization:** The entire system runs isolated in containers. Offers single-command setup, cross-platform compatibility, and production-ready deployment.
* **Redis Caching:** Repetitive queries are answered instantly. Achieved an **88% cache hit rate** and a **35x performance boost**.
* **PII Security:** Sensitive data (emails, phone numbers, ID numbers) is automatically detected and masked/redacted.

<img width="1918" height="900" alt="think ai security 1" src="https://github.com/user-attachments/assets/70124c08-31f0-4ea7-be4d-0bedf8a9d6b5" />

<img width="1002" height="157" alt="think ai security 2" src="https://github.com/user-attachments/assets/61c41872-bb02-4a50-ba39-d16113113fb0" />

---

## Tech Stack

The project is built on a modern and scalable technology stack:

* **Core:** Python 3.x, Asyncio (Asynchronous Architecture)
* **LLM Runtime:** Ollama (Localhost)
* **Models:** Qwen 2.5 (Analyst) & Gemma 2 (Critic)
* **AI & NLP:** PyTorch, Scikit-learn
* **Interface:** Gradio
* **Search & RAG:** DuckDuckGo Search, Sentence Transformers, NumPy
* **Container:** Docker
* **Cache:** Redis 7

---

<img width="1913" height="897" alt="think ai 1 " src="https://github.com/user-attachments/assets/54d95c40-6504-4800-b10a-3070f032e890" />
<img width="1461" height="867" alt="think ai 2" src="https://github.com/user-attachments/assets/2c4f8203-9208-4c7f-8d7a-b1fdfed9f3da" />

## Installation

Follow the steps below to run the project on your local machine.

### 1. Prerequisites

* **Docker Desktop** must be installed.
* Minimum **16 GB RAM** recommended.
* **15 GB free disk space**.

### 2. Quick Start

**Windows:**
```powershell
git clone [https://github.com/canberkdumann/Think_AI_Main.git](https://github.com/canberkdumann/Think_AI_Main.git)
cd Think_AI_Main
.\start.ps1
