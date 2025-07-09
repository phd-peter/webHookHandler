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

# Determine project root relative to this file (../)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

# Flask setup – adjust static/template folders for Vercel
app = Flask(
    __name__,
    static_folder=os.path.join(PROJECT_ROOT, "static"),
    template_folder=os.path.join(PROJECT_ROOT, "templates")
)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize OpenAI client
authorization_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=authorization_key)

# In-memory session storage for conversation history (stateless caveat)
SESSION_MEMORY = {}

class ConversationContext(BaseModel):
    conversation_history: list[dict] = []
    session_id: str = ""
    created_at: str = ""

# ----------------------------- AGENTS ----------------------------------

def web_search_agent(query: str) -> str:
    """Simulated web search agent – would integrate with real search API"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a web search specialist. For this query, provide information as if you just searched the web for current, real-time information. Be specific and informative."
                },
                {"role": "user", "content": f"Search for: {query}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
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
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an intelligent routing assistant. Analyze the user's question and decide which tool to use:\n\n"
                    "1. **Knowledge Base** - for company-specific information, internal docs, FAQs, policies\n"
                    "2. **Web Search** - for current events, real-time info, general knowledge, recent news\n\n"
                    "Respond with JSON in this exact format:\n"
                    "{\n    \"tool\": \"web_search\" or \"knowledge_base\",\n    \"reasoning\": \"Brief explanation of why this tool was chosen\",\n    \"query\": \"Processed query for the chosen tool\"\n}"
                )
            }
        ]

        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.append(msg)

        messages.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3
        )

        result = json.loads(response.choices[0].message.content)

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
        return {
            "response": web_search_agent(query),
            "tool_used": "web_search",
            "reasoning": "Fallback due to routing error",
            "processed_query": query
        }

# ----------------------------- ROUTES ----------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json or {}
        user_question = data.get("question", "").strip()
        session_id = data.get("session_id")

        if not user_question:
            return jsonify({"error": "No question provided"}), 400

        if not session_id:
            session_id = str(uuid.uuid4())

        logger.info(f"Processing question for session {session_id}: {user_question}")

        if session_id not in SESSION_MEMORY:
            SESSION_MEMORY[session_id] = ConversationContext(
                conversation_history=[],
                session_id=session_id,
                created_at=datetime.now().isoformat()
            )

        session_context = SESSION_MEMORY[session_id]

        user_message = {"content": user_question, "role": "user"}
        session_context.conversation_history.append(user_message)

        result = router_agent(user_question, session_context.conversation_history)

        response_text = result["response"] or "I apologize, but I couldn't generate a response. Please try rephrasing your question."

        assistant_message = {"content": response_text, "role": "assistant"}
        session_context.conversation_history.append(assistant_message)

        logger.info(
            f"Session {session_id} now has {len(session_context.conversation_history)} messages")

        return jsonify({
            "session_id": session_id,
            "question": user_question,
            "response": response_text,
            "tool_used": result.get("tool_used", "unknown"),
            "reasoning": result.get("reasoning", ""),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred while processing your request: {str(e)}"}), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
    try:
        sessions_info = [
            {
                "session_id": sid,
                "created_at": ctx.created_at,
                "message_count": len(ctx.conversation_history)
            } for sid, ctx in SESSION_MEMORY.items()
        ]
        return jsonify({"sessions": sessions_info, "total_sessions": len(sessions_info)})
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
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