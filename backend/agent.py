# backend/agent.py
import os
import json
import sqlite3
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage
from database import init_db

# Run the database initialization explicitly
init_db()

# Load the API key from the .env file
load_dotenv()

# Initialize the Groq LLM as required by the tech stack
llm = ChatGroq(
    # model="gemma2-9b-it", 
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# 1. Define the Schema (Added hcpSpecialty for invisible memory)
class InteractionFormSchema(BaseModel):
    hcpName: str = Field(default="", description="Name of the Healthcare Professional")
    hcpSpecialty: str = Field(default="Unknown", description="Specialty of the HCP if mentioned (e.g., cardiologist)")
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
def log_interaction(summary: str) -> str: # <--- Changed return type to str
    """
    Use this tool when the user provides an initial summary of a meeting to log a NEW interaction.
    It extracts all details into a structured JSON payload.
    """
    structured_llm = llm.with_structured_output(InteractionFormSchema)
    
    # We updated the prompt to strictly enforce the array rule
    prompt = f"Extract the meeting details from the following summary. IMPORTANT: For materialsShared and samplesDistributed, you MUST return a valid JSON array of strings, even if there is only one item. If none, return []. Summary: {summary}"
    
    result = structured_llm.invoke(prompt)
    
    # <--- We now explicitly convert the dictionary to a valid JSON string using json.dumps!
    return json.dumps({"action": "UPDATE_FORM", "data": result.dict()})

# 3. Define the Mandatory Tool 2: Edit Interaction
@tool
def edit_interaction(updates: dict) -> str: # <--- Changed return type to str
    """
    Use this tool to edit or update existing fields in the form.
    Pass a dictionary where the keys are the field names and values are the new values.
    Valid keys: hcpName, interactionType, date, time, attendees, topicsDiscussed, materialsShared, samplesDistributed, sentiment, outcomes, followUpActions.
    """
    # <--- We now explicitly convert the dictionary to a valid JSON string using json.dumps!
    return json.dumps({"action": "PATCH_FORM", "data": updates})

# 4. Custom Tool 1: Fetch HCP Profile (Now reads from Real DB)
@tool
def fetch_hcp_profile(hcp_name: str) -> str:
    """Fetches background information and past preferences for a given HCP."""
    conn = sqlite3.connect('crm_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT specialty, preferences FROM hcp_profiles WHERE name LIKE ?", (f"%{hcp_name}%",))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return f"Specialty: {result[0]}, Preferences: {result[1]}"
    return "No profile found in database. They might be a new contact."

# 5. Custom Tool 2: Search Materials (Now searches past interactions)
@tool
def search_materials(topic: str) -> str:
    """Searches the database to see what materials were shared in the past about a specific topic."""
    conn = sqlite3.connect('crm_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT hcp_name, materials FROM interactions WHERE topics LIKE ?", (f"%{topic}%",))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        history = [f"Shared {r[1]} with {r[0]}" for r in results]
        return "Past material history: " + " | ".join(history)
    return "No past materials found for this topic."

# NEW TOOL: Fetch Meeting History
@tool
def get_interaction_history(hcp_name: str) -> str:
    """Fetches the history of past meetings, dates, and topics for a specific HCP."""
    conn = sqlite3.connect('crm_data.db')
    cursor = conn.cursor()
    # We pull the date, topics, and materials from the interactions table
    cursor.execute("SELECT date, topics, materials FROM interactions WHERE hcp_name LIKE ?", (f"%{hcp_name}%",))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        history = [f"Date: {r[0]} | Topics: {r[1]} | Materials: {r[2]}" for r in results]
        return "Past Meetings:\n" + "\n".join(history)
    return "No past meetings found for this doctor."

# NEW TOOL: Save the Interaction to the Database
@tool
def save_interaction_to_db(hcp_name: str, date: str, topics: str, materials: str = "", inferred_specialty: str = "Unknown") -> str:
    """
    Saves the interaction data.
    IMPORTANT: Read the 'Current Form State' to find 'hcpSpecialty' and pass it exactly as 'inferred_specialty'.
    """
    conn = sqlite3.connect('crm_data.db')
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO interactions (hcp_name, date, topics, materials) VALUES (?, ?, ?, ?)", 
                    (hcp_name, date, topics, materials))
    
    cursor.execute("SELECT * FROM hcp_profiles WHERE name = ?", (hcp_name,))
    existing_profile = cursor.fetchone()
    
    if not existing_profile:
        cursor.execute("INSERT INTO hcp_profiles (name, specialty, preferences) VALUES (?, ?, 'Added via interaction log.')", 
                        (hcp_name, inferred_specialty))
    elif inferred_specialty != "Unknown":
        cursor.execute("UPDATE hcp_profiles SET specialty = ? WHERE name = ?", 
                        (inferred_specialty, hcp_name))
        
    conn.commit()
    conn.close()
    
    return json.dumps({"action": "RESET_FORM", "data": {}})

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
    generate_follow_up_tasks,
    save_interaction_to_db,
    get_interaction_history
]

# 7. Create the LangGraph Agent
system_prompt = """You are a CRM AI assistant. 
You cannot affect the system just by talking. You MUST execute your tools to perform actions.

WORKFLOW RULES:
1. Drafting: If the user provides meeting details -> EXECUTE 'log_interaction' or 'edit_interaction'.
2. Saving: If the user explicitly says "save" -> EXECUTE 'save_interaction_to_db'. 
3. Querying: If looking up info -> EXECUTE 'fetch_hcp_profile' or 'get_interaction_history'.

CRITICAL RULES:
1. Do NOT roleplay. You must actually trigger the tool.
2. After saving or logging, give a short, friendly confirmation.
3. AFTER FETCHING DATA (like a profile or history), YOU MUST WRITE THE ACTUAL FETCHED DATA IN YOUR TEXT REPLY SO THE USER CAN READ IT! Do not hide the data.
"""

# Just pass the LLM and tools
agent_executor = create_react_agent(llm, tools)

# 8. Define the function that FastAPI will call
def run_agent(user_message: str, current_state: dict):
    context_message = f"User Message: {user_message}\nCurrent Form State: {json.dumps(current_state)}"
    
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
            print(f"--- TOOL FIRED! Raw Output: {msg.content} ---") # <--- Added this line!
            try:
                # Smarter parsing: Only try to load JSON if the string contains our action key
                if isinstance(msg.content, str) and '"action":' in msg.content:
                    tool_data = json.loads(msg.content)
                    action_type = tool_data.get("action", "NONE")
                    extracted_data = tool_data.get("data", {})
            except Exception:
                pass
                
    print(f"\n--- BACKEND DEBUG ---")
    print(f"AI Text Reply: {ai_text}")
    print(f"Action Triggered: {action_type}")
    print(f"---------------------\n")
                
    return {
        "ai_response": ai_text,
        "action": action_type,
        "extracted_data": extracted_data
    }