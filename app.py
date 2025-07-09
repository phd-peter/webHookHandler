import os
import uuid
import asyncio
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# In-memory session storage for conversation history
SESSION_MEMORY = {}

# Define the assistant's memory structure
class ConversationContext(BaseModel):
    conversation_history: list[dict] = []
    session_id: str = ""
    created_at: str = ""

def web_search_agent(query: str) -> str:
    """Simulated web search agent - would integrate with real search API"""
    try:
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=query
        )
        return response.output_text
    except Exception as e:
        return f"Web search error: {str(e)}"

def knowledge_base_agent(query: str) -> str:
    """Simulated knowledge base search agent"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a knowledge base specialist. Answer based on internal company documentation, FAQs, policies, and procedures. If you don't have specific information, clearly state that."
                },
                {"role": "user", "content": f"Search knowledge base for: {query}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Knowledge base search error: {str(e)}"

def router_agent(query: str, conversation_history: list = None) -> dict:
    """Smart routing agent that decides which tool to use"""
    try:
        # Prepare conversation context
        messages = [
            {
                "role": "system",
                "content": """You are an intelligent routing assistant. Analyze the user's question and decide which tool to use:

1. **Knowledge Base** - for company-specific information, internal docs, FAQs, policies
2. **Web Search** - for current events, real-time info, general knowledge, recent news

Respond with JSON in this exact format:
{
    "tool": "web_search" or "knowledge_base",
    "reasoning": "Brief explanation of why this tool was chosen",
    "query": "Processed query for the chosen tool"
}"""
            }
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append(msg)
        
        messages.append({"role": "user", "content": query})
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Route to appropriate agent
        if result.get("tool") == "web_search":
            agent_response = web_search_agent(result.get("query", query))
        else:
            agent_response = knowledge_base_agent(result.get("query", query))
        
        return {
            "response": agent_response,
            "tool_used": result.get("tool"),
            "reasoning": result.get("reasoning"),
            "processed_query": result.get("query", query)
        }
        
    except Exception as e:
        logger.error(f"Router agent error: {e}")
        # Fallback to web search
        return {
            "response": web_search_agent(query),
            "tool_used": "web_search",
            "reasoning": "Fallback due to routing error",
            "processed_query": query
        }

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    """API endpoint to handle questions"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        user_question = data.get("question", "").strip()
        session_id = data.get("session_id", None)

        if not user_question:
            return jsonify({"error": "No question provided"}), 400
        
        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"Processing question for session {session_id}: {user_question}")

        # Retrieve or initialize session memory
        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = ConversationContext(
                conversation_history=[],
                session_id=session_id,
                created_at=datetime.now().isoformat()
            )

        session_context = SESSION_MEMORY[session_id]

        # Add user question to conversation history
        user_message = {"content": user_question, "role": "user"}
        session_context.conversation_history.append(user_message)

        # Run the router agent
        logger.debug(f"Running router agent for session {session_id}")
        result = router_agent(user_question, session_context.conversation_history)

        response_text = result["response"]
        tool_used = result.get("tool_used", "unknown")
        reasoning = result.get("reasoning", "")

        # Fallback response
        if not response_text:
            response_text = "I apologize, but I couldn't generate a response. Please try rephrasing your question."

        # Save response in conversation history
        assistant_message = {"content": response_text, "role": "assistant"}
        session_context.conversation_history.append(assistant_message)

        # Log session memory size for monitoring
        logger.info(f"Session {session_id} now has {len(session_context.conversation_history)} messages")

        return jsonify({
            "session_id": session_id,
            "question": user_question,
            "response": response_text,
            "tool_used": tool_used,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"An error occurred while processing your request: {str(e)}"
        }), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Get list of active sessions"""
    try:
        sessions_info = []
        for session_id, context in SESSION_MEMORY.items():
            sessions_info.append({
                "session_id": session_id,
                "created_at": context.created_at,
                "message_count": len(context.conversation_history)
            })
        
        return jsonify({
            "sessions": sessions_info,
            "total_sessions": len(sessions_info)
        })
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get specific session conversation history"""
    try:
        if session_id not in SESSION_MEMORY:
            return jsonify({"error": "Session not found"}), 404
        
        context = SESSION_MEMORY[session_id]
        return jsonify({
            "session_id": session_id,
            "created_at": context.created_at,
            "conversation_history": context.conversation_history
        })
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a specific session"""
    try:
        if session_id not in SESSION_MEMORY:
            return jsonify({"error": "Session not found"}), 404
        
        del SESSION_MEMORY[session_id]
        return jsonify({"message": f"Session {session_id} deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(SESSION_MEMORY)
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Ensure environment variables are loaded
    required_env_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.warning("The application may not work correctly without proper configuration")
    
    logger.info("Starting OpenAI Agents Multi-Agent System")
    logger.info(f"Server will be available at http://0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
