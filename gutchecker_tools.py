import os
from dotenv import load_dotenv
#from langchain.agents import Tool
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
import nest_asyncio

# Apply nest_asyncio to allow nested event loops if needed in your environment
nest_asyncio.apply()

# Load environment variables (e.g., SERPER_API_KEY)
load_dotenv(override=True)

# Initialize Serper Wrapper
serper = GoogleSerperAPIWrapper()

def flag_ingredient(ingredient_name: str, reason: str):
    """Flags a harmful ingredient and records the reason."""
    return f"FLAGGED: {ingredient_name}. REASON: {reason}"

async def get_all_tools():
    # Set headless=True for Hugging Face deployment
    async_browser = create_async_playwright_browser(headless=True) 
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=async_browser)
    pw_tools = toolkit.get_tools()
    
    tool_search = Tool(
        name="ingredient_researcher",
        func=serper.run,
        description="Search for food labels and nutritional additives."
    )
    
    tool_flag = Tool(
        name="flag_harmful_ingredient",
        func=flag_ingredient,
        description="Mark ingredients as dangerous for the UI."
    )
    
    return pw_tools + [tool_search, tool_flag], async_browser, None