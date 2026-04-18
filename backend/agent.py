# backend/agent.py
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
import json

# Load the API key from the .env file
load_dotenv()

# Initialize the Groq LLM as required by the tech stack
llm = ChatGroq(
    # model="gemma2-9b-it", 
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# 1. Define the Schema (Updated with strict array instructions and defaults)
class InteractionFormSchema(BaseModel):
    hcpName: str = Field(default="", description="Name of the Healthcare Professional")
    interactionType: str = Field(default="Meeting", description="Type of interaction, e.g., Meeting, Email, Call")
    date: str = Field(default="", description="Date of interaction in DD-MM-YYYY format")
    time: str = Field(default="", description="Time of interaction in HH:MM format")
    attendees: str = Field(default="", description="Other attendees present")
    topicsDiscussed: str = Field(default="", description="Summary of topics discussed")
    materialsShared: List[str] = Field(default_factory=list, description="MUST be a JSON array of strings. Use [] if none.")
    samplesDistributed: List[str] = Field(default_factory=list, description="MUST be a JSON array of strings. Use [] if none. Example: ['OncoBoost']")
    sentiment: str = Field(default="Neutral", description="Observed sentiment: Positive, Neutral, or Negative")
    outcomes: str = Field(default="", description="Key outcomes or agreements")
    followUpActions: str = Field(default="", description="Next steps or tasks to follow up on")

# 2. Define the Mandatory Tool 1: Log Interaction
@tool
def log_interaction(summary: str) -> dict:
    """
    Use this tool when the user provides an initial summary of a meeting to log a NEW interaction.
    It extracts all details into a structured JSON payload.
    """
    structured_llm = llm.with_structured_output(InteractionFormSchema)
    
    # We updated the prompt to strictly enforce the array rule
    prompt = f"Extract the meeting details from the following summary. IMPORTANT: For materialsShared and samplesDistributed, you MUST return a valid JSON array of strings, even if there is only one item. If none, return []. Summary: {summary}"
    
    result = structured_llm.invoke(prompt)
    return {"action": "UPDATE_FORM", "data": result.dict()}

# 3. Define the Mandatory Tool 2: Edit Interaction
@tool
def edit_interaction(updates: dict) -> dict:
    """
    Use this tool to edit or update existing fields in the form.
    Pass a dictionary where the keys are the field names and values are the new values.
    Valid keys: hcpName, interactionType, date, time, attendees, topicsDiscussed, materialsShared, samplesDistributed, sentiment, outcomes, followUpActions.
    """
    return {"action": "PATCH_FORM", "data": updates}

# 4. Custom Tool 1: Fetch HCP Profile
@tool
def fetch_hcp_profile(hcp_name: str) -> str:
    """Fetches background information and past preferences for a given HCP."""
    db = {
        "Dr. Smith": "Cardiologist. Prefers morning meetings. High prescriber of BetaBlock-X.",
        "Dr. Sharma": "Oncologist. Key opinion leader. Interested in Phase III trial data."
    }
    return db.get(hcp_name, "No profile found in database.")

# 5. Custom Tool 2: Search Materials
@tool
def search_materials(topic: str) -> List[str]:
    """Searches the database for available materials or brochures related to a topic."""
    if "cancer" in topic.lower() or "onco" in topic.lower():
        return ["OncoBoost Phase III PDF", "Oncology Care Guide"]
    return ["General Product Brochure"]

# 6. Custom Tool 3: Generate Follow-up Tasks
@tool
def generate_follow_up_tasks(outcomes: str) -> str:
    """Generates a suggested list of follow-up tasks based on meeting outcomes."""
    prompt = f"Based on these meeting outcomes, write a short, bulleted list of 2 follow-up tasks: {outcomes}"
    response = llm.invoke(prompt)
    return response.content

# Bundle them up for LangGraph
tools = [
    log_interaction, 
    edit_interaction, 
    fetch_hcp_profile, 
    search_materials, 
    generate_follow_up_tasks
]

# 7. Create the LangGraph Agent
system_prompt = """You are an AI assistant for a pharma sales rep. 
Your job is to help log Healthcare Professional (HCP) interactions into the CRM.
- If the user provides a summary of a meeting, use the 'log_interaction' tool to extract the data.
- If they want to change a specific field, use the 'edit_interaction' tool.
- Use other tools if they ask for information or follow-ups.

STRICT RULES:
1. ALWAYS use the provided tools to update the form. Do NOT just output JSON.
2. In your final text response to the user, speak like a normal, helpful human assistant. NEVER show raw JSON in your text responses."""

# Just pass the LLM and tools
agent_executor = create_react_agent(llm, tools)

# 8. Define the function that FastAPI will call
def run_agent(user_message: str, current_state: dict):
    context_message = f"User Message: {user_message}\nCurrent Form State: {json.dumps(current_state)}"
    
    # We now pass the SystemMessage directly into the graph's memory at runtime!
    inputs = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context_message)
        ]
    }
    response = agent_executor.invoke(inputs)
    
    # Extract the AI's conversational text reply
    ai_text = response["messages"][-1].content
    
    extracted_data = {}
    action_type = "NONE"
    
    # Scan the graph's internal messages to see if a tool was fired
    for msg in response["messages"]:
        if msg.type == "tool":
            try:
                tool_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(tool_data, dict) and "action" in tool_data:
                    action_type = tool_data["action"]
                    extracted_data = tool_data["data"]
            except Exception as e:
                print("Error parsing tool data:", e)
                
    return {
        "ai_response": ai_text,
        "action": action_type,
        "extracted_data": extracted_data
    }





# # 7. Create the LangGraph Agent
# system_prompt = """You are an AI assistant for a pharma sales rep. 
# Your job is to help log Healthcare Professional (HCP) interactions into the CRM.
# - If the user provides a summary of a meeting, use the 'log_interaction' tool to extract the data.
# - If they want to change a specific field, use the 'edit_interaction' tool.
# - Use other tools if they ask for information or follow-ups.
# Always be concise and helpful in your text responses."""

# # This binds the Groq LLM, our 5 tools, and the system prompt together into a graph
# agent_executor = create_react_agent(llm, tools, state_modifier=system_prompt)

# # 8. Define the function that FastAPI will call
# # 8. Define the function that FastAPI will call
# def run_agent(user_message: str, current_state: dict):
#     # INJECT THE CURRENT STATE: Now the AI knows what is currently in the form!
#     context_message = f"User Message: {user_message}\nCurrent Form State: {json.dumps(current_state)}"
    
#     inputs = {"messages": [HumanMessage(content=context_message)]}
#     response = agent_executor.invoke(inputs)
    
#     # Extract the AI's conversational text reply
#     ai_text = response["messages"][-1].content
    
#     extracted_data = {}
#     action_type = "NONE"
    
#     # Scan the graph's internal messages to see if a tool was fired
#     for msg in response["messages"]:
#         if msg.type == "tool":
#             try:
#                 tool_data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
#                 if isinstance(tool_data, dict) and "action" in tool_data:
#                     action_type = tool_data["action"]
#                     extracted_data = tool_data["data"]
#             except Exception as e:
#                 print("Error parsing tool data:", e)
                
#     return {
#         "ai_response": ai_text,
#         "action": action_type,
#         "extracted_data": extracted_data
#     }