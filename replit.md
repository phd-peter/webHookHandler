# Multi-Agent AI Assistant

## Overview

This is a Flask-based multi-agent AI assistant application that provides intelligent routing between different specialized agents (web search, knowledge base, and router) to handle user queries. The system uses OpenAI's GPT-4o model with custom agent implementations for web search and knowledge base search capabilities.

## Recent Changes (July 2025)
- ✓ Migrated from experimental OpenAI agents framework to stable OpenAI Python SDK
- ✓ Implemented custom multi-agent system using GPT-4o with JSON response formatting
- ✓ Added smart routing agent that decides between web search and knowledge base tools
- ✓ Successfully deployed and tested all API endpoints
- ✓ Confirmed HTTP request/response functionality with session management

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with async support
- **Language**: Python 3.x
- **Session Management**: In-memory session storage using dictionaries
- **Agent Framework**: OpenAI Agents with multi-agent orchestration
- **Configuration**: Environment variable-based configuration with .env file support

### Frontend Architecture
- **Technology**: Vanilla JavaScript with Bootstrap 5 (dark theme)
- **UI Framework**: Bootstrap with custom CSS styling
- **Communication**: AJAX/Fetch API for real-time chat interactions
- **Design Pattern**: Single Page Application (SPA) with responsive design

## Key Components

### Agent System
1. **Web Search Agent**: Handles real-time information queries using WebSearchTool
2. **Knowledge Base Agent**: Retrieves information from vector stores using FileSearchTool
3. **Router Agent**: Intelligently routes queries to appropriate specialized agents
4. **Session Context**: Maintains conversation history using Pydantic models

### Core Files
- `app.py`: Main Flask application with agent initialization and API endpoints
- `main.py`: Application entry point for deployment
- `templates/index.html`: Single-page chat interface
- `static/script.js`: Frontend JavaScript for chat functionality
- `static/style.css`: Custom styling and animations

### Tools Integration
- **WebSearchTool**: Configured with medium search context size
- **FileSearchTool**: Uses vector store IDs from environment variables
- **Handoff System**: Enables seamless agent-to-agent communication

## Data Flow

1. **User Input**: User submits question through web interface
2. **Session Management**: Flask creates/retrieves session context
3. **Agent Routing**: Router agent determines appropriate specialized agent
4. **Tool Execution**: Selected agent uses relevant tools (web search or file search)
5. **Response Generation**: Agent generates contextual response
6. **UI Update**: Frontend displays response with proper formatting and animations

## External Dependencies

### Python Packages
- `flask`: Web framework
- `pydantic`: Data validation and modeling
- `python-dotenv`: Environment variable management
- `agents`: OpenAI agents framework (custom import)
- `asyncio`: Asynchronous programming support
- `logging`: Application logging

### Frontend Dependencies
- Bootstrap 5 (CDN): UI framework with dark theme
- Font Awesome 6 (CDN): Icon library
- Native browser APIs: Fetch, DOM manipulation

### Environment Variables
- `SESSION_SECRET`: Flask session encryption key
- `VECTOR_STORE_ID`: Vector store identifier for file search
- Additional OpenAI API configuration (implied)

## Deployment Strategy

### Development Setup
- Flask development server on port 5000
- Debug mode enabled for development
- Hot reload support through Flask

### Production Considerations
- Environment-based configuration
- Session secret management
- Host binding to 0.0.0.0 for container deployment
- Logging configuration for monitoring

### Key Features
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Chat**: Instant messaging interface with loading states
- **Session Persistence**: Maintains conversation context
- **Health Monitoring**: Built-in health check functionality
- **Multi-agent Coordination**: Intelligent routing between specialized agents

### Architecture Benefits
- **Modularity**: Separate agents for different use cases
- **Scalability**: Memory-based session storage (easily replaceable)
- **Flexibility**: Environment-based configuration
- **User Experience**: Modern chat interface with animations and feedback