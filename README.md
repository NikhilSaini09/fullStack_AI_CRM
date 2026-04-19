# AI-First CRM HCP Module - Log Interaction Screen

## 📋 Project Overview
This project is an **AI-First Customer Relationship Management (CRM) system** tailored for Life Science field representatives to manage interactions with Healthcare Professionals (HCPs). 

The core operational rule of this application is an **AI-Driven UI**: The user cannot manually fill out the interaction form. Instead, all data entry, modifications, and database queries are handled through natural language via a conversational AI assistant on the right-hand panel.

## ⚠️ Important Note on AI Model Selection
The original technical requirement requested the use of the `gemma2-9b-it` model via the Groq API. However, Groq has officially **decommissioned** this model from their servers, making it impossible to access. 

Following the assignment's explicit fallback instructions (*"You may also consider llama-3.3-70b-versatile for context"*), this project successfully implements the LangGraph agent routing and JSON tool-calling using the highly capable **`llama-3.3-70b-versatile`** model instead.

## 🛠️ Tech Stack
* **Frontend:** React.js, Redux (State Management), CSS (Google Inter font)
* **Backend:** Python, FastAPI
* **AI Agent Framework:** LangGraph & LangChain
* **LLM:** Groq API (`llama-3.3-70b-versatile`)
* **Database:** SQLite (Used for rapid local deployment; structured to easily migrate to MySQL/Postgres)

## ✨ Key Features
* **Split-Screen Interface:** A read-only interaction form on the left, completely controlled by the LangGraph AI agent on the right.
* **Intelligent State Management:** The AI dynamically updates the React frontend via Redux (`UPDATE_FORM`, `PATCH_FORM`, `RESET_FORM` actions) before permanently committing data to the database.
* **Anti-Hallucination Guardrails:** The LLM is strictly prompted to execute background JSON tools rather than guessing data, preventing "LLM Amnesia" by reading the hidden Redux state.
* **Polished Enterprise UI:** Features suggested quick-prompts, dynamic sentiment radio buttons, and read-only inputs that mimic industry-standard platforms like Veeva or Salesforce Health Cloud.

## LangGraph AI Tools
The LangGraph agent is equipped with specific tools to route intents and manage the CRM:

1.  **`log_interaction` (Mandatory):** Extracts natural language summaries (e.g., "Met with Dr. Smith...") into a structured JSON payload to update the frontend form.
2.  **`edit_interaction` (Mandatory):** Allows the user to patch specific fields (e.g., "Change the sentiment to neutral") without erasing the rest of the form state.
3.  **`save_interaction_to_db`:** Commits the current Redux form state to the SQLite database. It also intelligently extracts any mentioned specialty and creates/updates the HCP's permanent profile.
4.  **`fetch_hcp_profile`:** Queries the database for a specific doctor's static profile (Specialty, Preferences) and returns it to the chat.
5.  **`get_interaction_history`:** Queries the database for past meeting dates, topics, and materials for a specific HCP.
6.  **`search_materials` / `generate_follow_up_tasks`:** Additional utilities for finding past brochures or generating AI-driven task lists based on meeting outcomes.


---

## Setup & Installation Instructions

### 1. Clone the Repository
git clone <your-repo-url>
cd ai-crm-hcp

### 2. Backend Setup
Navigate to the backend directory, create a virtual environment, and install dependencies:

cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

Create a `.env` file in the `backend` directory and add your Groq API Key:
GROQ_API_KEY=your_groq_api_key_here

Run the FastAPI Server:
uvicorn main:app --reload

*The API will be available at http://localhost:8000. The SQLite database (`crm_data.db`) will auto-generate on the first run.*


### 3. Frontend Setup
Open a new terminal window:

cd frontend
npm install
npm start

*The React app will launch at http://localhost:3000.*

---

## Usage Examples (Prompts to Try)
Use the AI Assistant chat panel to control the application:

* **Log a Meeting:** *"Met with Dr. Strange today. He is a neurologist. We discussed brain health. Sentiment was positive. I gave him the brain brochure."*
* **Edit the Form:** *"Actually, change the sentiment to Neutral."*
* **Save to Database:** *"Looks good, save it."*
* **Query Profile:** *"What is Dr. Strange's specialty?"*
* **Query History:** *"When did I last meet with Dr. Strange and what did we discuss?"*
