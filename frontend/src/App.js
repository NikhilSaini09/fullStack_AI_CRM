import React, { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { updateForm } from './redux/interactionSlice';
import './App.css';

function App() {
  // Read state from Redux
  const formState = useSelector((state) => state.interaction);
  const dispatch = useDispatch();
  
  // Local state for the chat window
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hi! I am your AI assistant. Tell me about your HCP interaction, and I will log it for you.' }
  ]);

  // const handleSendMessage = () => {
  //   if (!chatInput.trim()) return;
    
  //   // Add user message to UI
  //   setMessages(prev => [...prev, { role: 'user', text: chatInput }]);
    
  //   // TODO: We will hook this up to the FastAPI backend in Phase 3
  //   console.log("Sending to backend:", chatInput);
    
  //   setChatInput('');
  // };
  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    
    // Add user message to UI immediately
    const userMsg = chatInput;
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatInput(''); // Clear input box

    try {
      // Send the message and the current form state to FastAPI
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg,
          current_state: formState 
        })
      });

      const data = await response.json();

      // Add the AI's reply to the chat window
      setMessages(prev => [...prev, { role: 'ai', text: data.ai_response }]);
      
      // If the AI sent back form data, we will dispatch it to Redux here later!
      if (data.action === "UPDATE_FORM" || data.action === "PATCH_FORM") {
        dispatch(updateForm(data.extracted_data));
      }

    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, { role: 'ai', text: 'Error: Could not reach the server.' }]);
    }
  };

  return (
    <div className="app-container">
      
      {/* LEFT PANEL: The Read-Only Form */}
      <div className="left-panel">
        <h2 style={{ marginBottom: '20px' }}>Log HCP Interaction</h2>
        
        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>HCP Name</label>
            <input type="text" value={formState.hcpName} readOnly disabled />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Interaction Type</label>
            <input type="text" value={formState.interactionType} readOnly disabled />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '20px' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Date</label>
            <input type="text" value={formState.date} readOnly disabled />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Time</label>
            <input type="text" value={formState.time} readOnly disabled />
          </div>
        </div>

        <div className="form-group">
          <label>Topics Discussed</label>
          <textarea rows="4" value={formState.topicsDiscussed} readOnly disabled />
        </div>

        <div className="form-group">
          <label>Sentiment</label>
          <input type="text" value={formState.sentiment} readOnly disabled />
        </div>

        <div className="form-group">
          <label>Follow-up Actions</label>
          <textarea rows="3" value={formState.followUpActions} readOnly disabled />
        </div>
      </div>

      {/* RIGHT PANEL: The AI Chat */}
      <div className="right-panel">
        <h3 style={{ marginBottom: '16px', color: '#1d4ed8' }}>AI Assistant</h3>
        
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
                maxWidth: '80%'
              }}>
                {msg.text}
              </span>
            </div>
          ))}
        </div>

        <div className="chat-input-area">
          <input 
            type="text" 
            placeholder="Describe interaction..." 
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