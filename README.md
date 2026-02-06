# GutCheck: The AI Ingredient Police

**GutCheck** is an intelligent agentic workflow built to analyze food products for harmful additives. Unlike generic chatbots, GutCheck uses a directed graph architecture to strictly evaluate ingredients, research their health effects in real-time, and flag "red flag" items based on a custom safety score.

> *Built with LangGraph, LangChain, and OpenAI.*

## Architecture (The Backend)

The core logic is built on **LangGraph**, treating the conversation as a state machine rather than a simple chain.

### 1. The Brain (`nutritionist_node`)
- **Model:** GPT-4o-mini
- **Persona:** A strict, blunt nutritionist. It does not "chat"; it analyzes.
- **System Prompt:** "You are 'GutCheck'. Use tools to research ingredients and alert users to dangers."

### 2. The Tools
- **`ingredient_researcher`**: A custom wrapper around Google Serper API. It doesn't just "search web"; it targets nutritional databases and ingredient safety sheets.
- **`flag_harmful_ingredient`** (In Progress): A state-modifying tool that updates the `flagged_ingredients` array and lowers the product's `safety_score` instead of just printing text.

### 3. State Management & Memory
- **Persistence:** Uses `SqliteSaver` (SQLite) to maintain conversation threads.
- **Memory:** The agent remembers previous ingredients scanned in the session to perform comparative analysis (e.g., "This bar is worse than the one you showed me 10 minutes ago").
- **Human-in-the-Loop:** (Upcoming) Implements `interrupt_before` logic to require user approval before flagging controversial ingredients (like Palm Oil).

## Current Status

- [x] **Day 1: The Graph:** Basic StateGraph with `nutritionist` and `tools` nodes.
- [x] **Day 2: The Hardware:** Integrated Search APIs and Alert mechanisms.
- [x] **Day 3: Memory:** Implemented Long-Term Persistence (Thread IDs).
- [ ] **Day 4: Custom State:** Currently building structured state (`TypedDict`) to track `safety_scores`.
- [ ] **Day 5: The Frontend:** Planned `ui_architect` agent to auto-generate a Gradio/Hugging Face interface.

## Tech Stack
- **Orchestration:** LangGraph, LangChain
- **LLM:** OpenAI GPT-4o-mini
- **Tools:** Google Serper (Search), Pushover (Notifications - *Deprecated for UI display*)
- **Database:** SQLite (Checkpointer)