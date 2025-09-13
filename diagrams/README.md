# Componion System Diagrams

This directory contains comprehensive PlantUML diagrams describing the entire Componion video study assistant system.

## Diagram Files

### 1. `system_overview.puml`
**High-level system architecture** showing all major components and their relationships:
- Frontend React components
- Backend Flask + SocketIO services
- External APIs (Gemini, TMDB, YouTube)
- Database schema overview
- Data flow between components

### 2. `database_schema.puml`
**Complete database schema** with all tables and relationships:
- `sessions` - Video study sessions
- `session_users` - Real-time user presence
- `chat_messages` - Chat history with AI integration
- `video_analysis` - AI-processed video content
- `tv_show_info` - TMDB metadata
- `video_processing_status` - Processing pipeline status

### 3. `ai_context_flow.puml`
**AI Context Enhancement Flow** showing the intelligent ContextAgent:
- User question analysis
- Context decision making
- TMDB data fetching
- Prompt construction
- AI response generation
- Shows how the system decides what additional context to fetch

### 4. `video_processing_flow.puml`
**Video Processing Pipeline** from YouTube URL to AI-ready content:
- YouTube video extraction
- Audio transcription
- Screenshot analysis
- Content identification
- TMDB metadata enrichment
- Real-time status updates

### 5. `realtime_communication.puml`
**WebSocket Communication** for real-time features:
- User session management
- Real-time chat with AI integration
- Video synchronization between master and participants
- User presence and notifications

### 6. `frontend_architecture.puml`
**React Frontend Architecture** showing component relationships:
- Component hierarchy
- Service layer (Socket, API)
- State management patterns
- Navigation flow

### 7. `backend_architecture.puml`
**Flask Backend Architecture** showing service organization:
- API layer (REST endpoints)
- WebSocket layer (real-time events)
- Core services (AI, video processing)
- External API integrations
- Database layer

### 8. `user_journey.puml`
**Complete User Journey** from start to finish:
- Session creation/joining
- Video processing flow
- Master vs participant experiences
- AI chat interaction
- Video synchronization

## How to View Diagrams

### Online Viewers
1. **PlantUML Server**: Copy diagram content to http://www.plantuml.com/plantuml/
2. **VS Code Extension**: Install "PlantUML" extension for live preview
3. **IntelliJ IDEA**: Built-in PlantUML support

### Local Generation
```bash
# Install PlantUML
npm install -g plantuml

# Generate all diagrams as PNG
plantuml diagrams/*.puml

# Generate as SVG
plantuml -tsvg diagrams/*.puml
```

## System Highlights

### 🤖 **ContextAgent Intelligence**
The ContextAgent analyzes user questions to intelligently decide what additional context to fetch from TMDB:
- "Who plays X?" → fetches cast information
- "Similar shows?" → fetches recommendations  
- "How many seasons?" → fetches season data
- "Who created this?" → fetches production details

### 🎬 **Video Processing Pipeline**
Automated processing of YouTube videos:
- Audio extraction and transcription
- Screenshot analysis with AI
- Content identification and TMDB lookup
- Real-time progress tracking

### 🔄 **Real-time Synchronization**
Master-participant video synchronization:
- Master controls playback
- Automatic time broadcasting
- Participant sync requests
- Real-time chat integration

### 💬 **AI-Enhanced Chat**
Context-aware AI assistant:
- Video timestamp context
- Show/movie metadata
- Chat history awareness
- Enhanced TMDB information

## Architecture Principles

- **Microservice-oriented**: Clear separation of concerns
- **Real-time first**: WebSocket-based communication
- **AI-native**: Integrated AI throughout the pipeline
- **Context-aware**: Intelligent context enhancement
- **Scalable**: Async processing and efficient data flow
