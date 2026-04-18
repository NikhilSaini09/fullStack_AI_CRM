# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import run_agent  # Import our new LangGraph function!

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    current_state: dict

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"Processing message: {request.message}")
    
    # Pass the message to our LangGraph agent
    result = run_agent(request.message, request.current_state)
    
    # Send the AI text and the extracted JSON data back to React
    return result










# # backend/main.py
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# app = FastAPI()

# # Allow React frontend to communicate with this backend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # React app's URL
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Define what the incoming data looks like
# class ChatRequest(BaseModel):
#     message: str
#     current_state: dict

# @app.post("/api/chat")
# async def chat_endpoint(request: ChatRequest):
#     print(f"Received message from React: {request.message}")
#     print(f"Current Form State: {request.current_state}")
    
#     # For now, we return a dummy response. 
#     # In Phase 4, LangGraph will generate this response and extract the JSON.
#     return {
#         "ai_response": f"I received your message: '{request.message}'. I will process this with LangGraph soon!",
#         "extracted_data": {
#             # We will send back structured data here later to update the form
#         }
#     }