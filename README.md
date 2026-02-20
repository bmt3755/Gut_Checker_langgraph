---
title: GutChecker
emoji: 🛡️
colorFrom: green
colorTo: purple
sdk: gradio
app_file: app.py
pinned: false
---
# GutChecker: Agentic Food Safety Auditor

GutChecker is a high-precision, multi-agent workflow designed to analyze food products for harmful additives. Moving beyond standard linear LLM prompts, this system utilizes a self-correcting Manager-Worker architecture to scrape live product data, cross-reference nutritional safety databases, and enforce strict mathematical and formatting rules.

## System Architecture

The core logic is implemented as a cyclical state machine using LangGraph.



### 1. The Worker (Nutritionist Node)
The primary research agent powered by GPT-4o-mini. 
* **Tools Used:** Async Playwright (for DOM scraping) and Google Serper API (for chemical additive research).
* **Task:** Identifies all ingredients, assigns a 1-10 safety score for controversial items, and calculates the mathematical average.

### 2. The Evaluator (Manager Node)
The quality control auditor that grades the Worker's output using Pydantic structured outputs.
* **Validation:** Enforces strict output formatting, verifies mathematical accuracy, and ensures the final summary is strictly one sentence.
* **Feedback Loop:** If criteria are not met, the Evaluator intercepts the payload, appends specific correction instructions to the state, and routes the task back to the Worker.

### 3. State Management & UI
* **Persistence:** `MemorySaver` tracks multi-turn conversation threads.
* **Resource Management:** Custom Object-Oriented wrapper (`GutChecker` class) ensures the headless Playwright browser instances are safely closed upon session termination to prevent memory leaks.
* **Frontend:** Gradio Blocks API mapped to asynchronous process callbacks.

## Tech Stack
* **Orchestration:** LangGraph, LangChain
* **LLMs:** OpenAI GPT-4o-mini
* **Search & Scraping:** Serper.dev, Playwright (Async)
* **Frontend:** Gradio

---

## Local Setup & Installation

Follow these steps to run GutChecker on your local machine.

### 1. Clone the Repository
Download the project files to your local system.
```bash
git clone <your-repository-url>
cd GutChecker

```

### 2. Set Up a Virtual Environment (Recommended)

Create and activate a clean Python environment.

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

```

### 3. Install Dependencies

Install the required Python packages.

```bash
pip install -r requirements.txt

```

### 4. Install Playwright Browsers

The agent requires a local headless browser to read ingredient websites.

```bash
playwright install chromium

```

### 5. Configure Environment Variables

Create a `.env` file in the root directory and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here

```

### 6. Run the Application

Launch the Gradio interface.

```bash
python app.py

```

The terminal will provide a local URL. Open the link in your browser to start using GutChecker.

```
