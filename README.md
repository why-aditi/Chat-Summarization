# ChatInsight - Chat Summarization and Insights Platform

A powerful platform that combines a FastAPI backend with a Streamlit frontend to process chat data, generate summaries, and provide real-time insights using Google's Gemini API.

## Features

- Real-time chat processing with WebSocket support
- MongoDB-based chat storage and retrieval
- Advanced chat summarization using Gemini API
- Sentiment analysis and keyword extraction
- Streamlit-based interactive UI
- RESTful API endpoints for chat operations
- Efficient pagination and filtering capabilities

## Architecture

ChatInsight follows a microservices architecture with two main components:

### Backend (FastAPI)

- RESTful API endpoints for chat operations
- WebSocket server for real-time communication
- MongoDB integration for data persistence
- Gemini API integration for AI-powered features
- Asynchronous processing for improved performance

### Frontend (Streamlit)

- Interactive web interface for chat visualization
- Real-time updates via WebSocket connection
- Responsive design for various screen sizes
- Data visualization components
- User-friendly chat management interface

## Prerequisites

- Python 3.11 or higher
- MongoDB instance (local or cloud)
- Google Cloud account for Gemini API access

## Installation

### Local Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/why-aditi/chatinsight.git
   cd chatinsight
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Unix or MacOS
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the backend directory with the following variables:
   ```env
   MONGODB_URL=your_mongodb_connection_string
   GEMINI_API_KEY=your_gemini_api_key
   ```

### Docker Setup

1. Build the Docker image:

   ```bash
   docker build -t chatinsight .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -p 8501:8501 chatinsight
   ```

## Usage

### Running the Backend

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   The API will be available at `http://localhost:8000`

### Running the Frontend

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Launch the Streamlit app:
   ```bash
   streamlit run app.py
   ```
   The UI will be available at `http://localhost:8501`

## API Documentation

Once the backend is running, access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Available Endpoints

- `POST /chats` - Create a new chat message
- `GET /chats/{conversation_id}` - Retrieve conversation history
- `GET /chats/users/{user_id}/messages` - Get user's chat history (paginated)
- `POST /chats/summarize` - Generate conversation summary
- `DELETE /chats/{conversation_id}` - Delete a conversation
- `WebSocket /chats/ws/{client_id}` - Real-time chat connection

### Project Structure

```
├── backend/
│   ├── app/
│   │   ├── config.py         # Configuration settings
│   │   ├── database.py       # Database connections
│   │   ├── main.py          # FastAPI application
│   │   ├── models/          # Data models and schemas
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   └── streamlit_app.py # Streamlit dashboard application
├── frontend/
│   └── app.py              # Streamlit chat interface
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-container orchestration
├── supervisord.conf        # Process management config
└── requirements.txt        # Python dependencies
```
