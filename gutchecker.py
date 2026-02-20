from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
import uuid
import asyncio

from gutchecker_tools import get_all_tools 

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool

class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Evaluation of the ingredient analysis.")
    success_criteria_met: bool = Field(description="True if math and formatting are correct.")
    user_input_needed: bool = Field(description="True if the agent needs human help.")

class GutChecker:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.graph = None
        self.thread_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.browser = None

    async def setup(self):
        self.tools, self.browser = await get_all_tools()
        
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        #self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput, 
            method="function_calling"
        )
        
        await self.build_graph()

#     def worker(self, state: State) -> Dict[str, Any]:
#         system_message = f"""### CORE MISSION ### 
# You are a Professional Nutritionist and Food Safety Auditor. 
# Your goal is to fulfill this Success Criteria: {state['success_criteria']}

# ### MANDATORY RATING RULES ###
# - Rate every controversial additive 1-10 (1 = Toxic, 10 = Safe).
# - SCORING MATH: Your 'Final Score' must be the average of the additive scores. Show the math briefly.

# ### MISSION INSTRUCTIONS ###
# 1. Use 'navigate_browser' for ingredient lists.
# 2. Use 'ingredient_researcher' for health risks.
# 3. Use 'flag_harmful_ingredient' for any additive scoring below 7.

# ### RESPONSE FORMAT (STRICT) ###
# - Additive: Score/10 - Short reason.
# - Final Score: X/10 (Brief math explanation).
# - Bottom Line: One sentence maximum."""

#         if state.get("feedback_on_work"):
#             system_message += f"\n\n### PRIOR FEEDBACK ###\nFix these issues: {state['feedback_on_work']}"

#         messages = state["messages"]
#         found = False
#         for msg in messages:
#             if isinstance(msg, SystemMessage):
#                 msg.content = system_message
#                 found = True
#         if not found:
#             messages = [SystemMessage(content=system_message)] + messages

#         response = self.worker_llm_with_tools.invoke(messages)
#         return {"messages": [response]}

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""### CORE MISSION ### 
You are 'GutCheck', a blunt Health Auditor. Your goal is to expose the metabolic reality of products.
Success Criteria: {state['success_criteria']}

### MANDATORY AUDIT RULES ###
1. **The "Sugar-First" Rule:** If sugar, syrup, or caloric sweeteners are in the top 3 ingredients, it is a 'Metabolic Tax' (Max score 3/10).
2. **Industrial Oil Flagging:** Specifically identify and penalize refined oils: Palm, Soybean, Canola, Corn, Safflower, and Sunflower. 
3. **Macronutrient Research:** You MUST use 'ingredient_researcher' to find the 'Added Sugar' and 'Saturated Fat' grams per serving. 
   - If added sugar > 10g: Automatic -3 penalty to the final score.

### SCORING MATH ###
- Start with a Base of 10.
- Subtract points for high sugar, industrial oils, and harmful additives.
- Show the subtraction math clearly.

### RESPONSE FORMAT (STRICT) ###
- Flagged Ingredients: List offenders + 1-word reason (e.g., "Palm Oil: Inflammatory").
- Macro Audit: Grams of Sugar and Fat found.
- Score Calculation: Show the deduction math.
- Bottom Line: One sentence maximum."""

        if state.get("feedback_on_work"):
            system_message += f"\n\n### PRIOR FEEDBACK ###\nFix these issues: {state['feedback_on_work']}"

        messages = state["messages"]
        found = False
        for msg in messages:
            if isinstance(msg, SystemMessage):
                msg.content = system_message
                found = True
        if not found:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_history(self, messages: List[Any]) -> str:
        convo = "History:\n\n"
        for m in messages:
            if isinstance(m, HumanMessage): convo += f"User: {m.content}\n"
            elif isinstance(m, AIMessage): convo += f"Assistant: {m.content or '[Tools]'}\n"
        return convo

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content
        sys_msg = "You determine if the Assistant followed all formatting, math, and strictness rules."
        
        user_msg = f"""
        History: {self.format_history(state['messages'])}
        Criteria: {state['success_criteria']}
        Final Response to Grade: {last_response}
        
        INSTRUCTIONS: Decide if criteria are met. If summary is > 1 sentence, reject it. If math is wrong, reject it.
        """
        if state["feedback_on_work"]:
            user_msg += f"Previous Feedback ignored: {state['feedback_on_work']}. Ask for user input if stuck."

        result = self.evaluator_llm_with_output.invoke([SystemMessage(content=sys_msg), HumanMessage(content=user_msg)])
        
        return {
            "messages": [AIMessage(content=f"Evaluator Feedback: {result.feedback}")],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed
        }

    def eval_router(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]: 
            return "END"
        return "worker"

    async def build_graph(self):
        builder = StateGraph(State)
        builder.add_node("worker", self.worker)
        builder.add_node("tools", ToolNode(tools=self.tools))
        builder.add_node("evaluator", self.evaluator)
        
        builder.add_conditional_edges("worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"})
        builder.add_edge("tools", "worker")
        builder.add_conditional_edges("evaluator", self.eval_router, {"worker": "worker", "END": END})
        builder.add_edge(START, "worker")
        
        self.graph = builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        if not self.graph:
            await self.setup()
            
        config = {"configurable": {"thread_id": self.thread_id}}
        
        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria or "Analyze product safety. Calculate average score. Keep summary under 1 sentence.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        
        result = await self.graph.ainvoke(state, config=config)
        
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        
        return history + [user, reply]

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
            except RuntimeError:
                asyncio.run(self.browser.close())