import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { updateForm, resetForm } from './redux/interactionSlice';
import './App.css';

function App() {
  const formState = useSelector((state) => state.interaction);
  const dispatch = useDispatch();
  
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hi! I am your AI assistant. Tell me about your HCP interaction, and I will log it for you.' }
  ]);

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = chatInput;
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatInput(''); 

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg,
          current_state: formState 
        })
      });

      const data = await response.json();

      setMessages(prev => [...prev, { role: 'ai', text: data.ai_response }]);
      
      if (data.action === "UPDATE_FORM" || data.action === "PATCH_FORM") {
        dispatch(updateForm(data.extracted_data));
      } else if (data.action === "RESET_FORM") {
        dispatch(resetForm()); 
      }
      
    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, { role: 'ai', text: 'Error: Could not reach the server.' }]);
    }
  };

  // Helper to format sentiment strings for radio checking
  const currentSentiment = formState.sentiment ? formState.sentiment.toLowerCase() : 'neutral';

  return (
    <div className="app-container">
      
      {/* LEFT PANEL: The Read-Only Form */}
      <div className="left-panel">
        <h2 style={{ marginBottom: '20px', color: '#1f2937' }}>Log HCP Interaction</h2>
        
        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>HCP Name</label>
            <input type="text" value={formState.hcpName} readOnly disabled placeholder="Search or select HCP..." />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Interaction Type</label>
            <input type="text" value={formState.interactionType} readOnly disabled />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Date</label>
            <div className="input-with-icon">
              <input type="text" value={formState.date} readOnly disabled placeholder="DD-MM-YYYY" />
              <span className="input-icon">📅</span>
            </div>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Time</label>
            <div className="input-with-icon">
              <input type="text" value={formState.time} readOnly disabled placeholder="HH:MM" />
              <span className="input-icon">🕒</span>
            </div>
          </div>
        </div>

        {/* Added Attendees Section */}
        <div className="form-group">
          <label>Attendees</label>
          <input type="text" value={formState.attendees} readOnly disabled placeholder="Enter names or search..." />
        </div>

        <div className="form-group">
          <label>Topics Discussed</label>
          <textarea rows="3" value={formState.topicsDiscussed} readOnly disabled placeholder="Enter key discussion points..." />
        </div>

        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Materials Shared</label>
            <input type="text" value={formState.materialsShared.join(', ')} readOnly disabled placeholder="No materials added." />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Samples Distributed</label>
            <input type="text" value={formState.samplesDistributed.join(', ')} readOnly disabled placeholder="No samples added." />
          </div>
        </div>

        {/* Updated Sentiment Section with Radio Buttons */}
        <div className="form-group">
          <label>Observed/Inferred HCP Sentiment</label>
          <div className="sentiment-row">
            <label className="radio-label">
              <input type="radio" checked={currentSentiment === 'positive'} readOnly disabled />
              <span>😊 Positive</span>
            </label>
            <label className="radio-label">
              <input type="radio" checked={currentSentiment === 'neutral'} readOnly disabled />
              <span>😐 Neutral</span>
            </label>
            <label className="radio-label">
              <input type="radio" checked={currentSentiment === 'negative'} readOnly disabled />
              <span>😞 Negative</span>
            </label>
          </div>
        </div>

        <div className="form-group">
          <label>Follow-up Actions</label>
          <textarea rows="2" value={formState.followUpActions} readOnly disabled placeholder="Enter next steps or tasks..." />
        </div>

        {/* Suggested AI Prompts for the user */}
        <div className="suggested-prompts">
          <label>AI Suggested Prompts:</label>
          <button className="prompt-btn" onClick={() => setChatInput("Met with Dr. Smith today. We discussed product X. Sentiment was positive.")}>
            + Log Interaction: "Met with Dr. Smith today..."
          </button>
          <button className="prompt-btn" onClick={() => setChatInput("Change the sentiment to Neutral.")}>
            + Edit Interaction: "Change the sentiment to Neutral."
          </button>
          <button className="prompt-btn" onClick={() => setChatInput("What background info do we have on Dr. Strange?")}>
            + Fetch Profile: "What background info do we have on Dr. Strange?"
          </button>
          <button className="prompt-btn" onClick={() => setChatInput("When did I last meet with Dr. Smith and what did we discuss?")}>
            + Fetch History: "When did I last meet with Dr. Smith..."
          </button>
          <button className="prompt-btn" onClick={() => setChatInput("Looks good, save it.")}>
            + Save to Database: "Looks good, save it."
          </button>
        </div>

      </div>

      {/* RIGHT PANEL: The AI Chat */}
      <div className="right-panel">
        <div className="chat-header">
          <span>🤖</span>
          <span>AI Assistant</span>
        </div>
        <p style={{fontSize: '12px', color: '#6b7280', marginTop: '-12px', marginBottom: '16px'}}>
          Log Interaction details here via chat
        </p>
        
        <div className="chat-history">
          {messages.map((msg, idx) => (
            <div key={idx} style={{ 
              marginBottom: '12px', 
              textAlign: msg.role === 'user' ? 'right' : 'left' 
            }}>
              <span style={{
                display: 'inline-block',
                padding: '10px 14px',
                borderRadius: '16px',
                backgroundColor: msg.role === 'user' ? '#dbeafe' : '#f3f4f6',
                color: '#1f2937',
                maxWidth: '85%',
                fontSize: '14px',
                lineHeight: '1.4'
              }}>
                {msg.text}
              </span>
            </div>
          ))}
        </div>

        <div className="chat-input-area">
          <input 
            type="text" 
            placeholder="Describe Interaction..." 
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          />
          <button onClick={handleSendMessage}>Log</button>
        </div>
      </div>

    </div>
  );
}

export default App;