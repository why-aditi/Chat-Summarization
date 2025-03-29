import streamlit as st
import requests
import json
from datetime import datetime
import asyncio
import websockets
from collections import defaultdict
import threading

# Configure the API URL
API_URL = "http://localhost:8000"

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user"
if 'insights' not in st.session_state:
    st.session_state.insights = defaultdict(lambda: {'sentiment': 'neutral', 'keywords': []})

# Page config
st.set_page_config(page_title="Chat Summarization Demo", layout="wide")
st.title("Chat Summarization and Insights Demo")

# Create two columns: one for chat, one for insights
chat_col, insights_col = st.columns([2, 1])

# Sidebar for settings and actions
with st.sidebar:
    st.header("Chat Settings")
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
    st.session_state.conversation_id = st.text_input("Conversation ID", value=st.session_state.conversation_id)
    
    if st.button("New Conversation"):
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []
        st.rerun()
    
    st.header("Analysis Options")
    include_sentiment = st.checkbox("Include Sentiment Analysis")
    include_keywords = st.checkbox("Include Keyword Extraction")
    
    if st.button("Generate Summary") and st.session_state.messages:
        with st.spinner("Generating summary..."):
            try:
                response = requests.post(
                    f"{API_URL}/chats/summarize",
                    json={
                        "conversation_id": st.session_state.conversation_id,
                        "include_sentiment": include_sentiment,
                        "include_keywords": include_keywords
                    }
                )
                if response.status_code == 200:
                    summary = response.json()
                    st.success("Summary generated successfully!")
                    st.text_area("Summary", summary["summary"], height=150)
                    if include_sentiment:
                        st.info(f"Sentiment: {summary['sentiment']}")
                    if include_keywords:
                        st.info(f"Keywords: {', '.join(summary['keywords'])}")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Main chat interface
with chat_col:
    st.header("Chat Interface")
    
    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["user_id"] == st.session_state.user_id else "assistant"):
            st.write(msg["message"])
            if msg["user_id"] in st.session_state.insights:
                insight = st.session_state.insights[msg["user_id"]]
                with st.expander("Message Insights"):
                    st.write(f"Sentiment: {insight['sentiment']}")
                    st.write(f"Keywords: {', '.join(insight['keywords'])}")

# Insights visualization
with insights_col:
    st.header("Conversation Insights")
    
    # Sentiment distribution
    sentiment_counts = defaultdict(int)
    for insight in st.session_state.insights.values():
        sentiment_counts[insight['sentiment']] += 1
    
    st.subheader("Sentiment Distribution")
    st.bar_chart(sentiment_counts)
    
    # Keywords word cloud
    st.subheader("Key Topics")
    all_keywords = set()
    for insight in st.session_state.insights.values():
        all_keywords.update(insight['keywords'])
    
    if all_keywords:
        st.write(", ".join(sorted(all_keywords)))

# Chat input
if prompt := st.chat_input("Type your message here"):
    # Add user message to chat
    message = {
        "conversation_id": st.session_state.conversation_id,
        "user_id": st.session_state.user_id,
        "message": prompt,
        "timestamp": datetime.now().isoformat(),
        "metadata": {}
    }
    
    # Send message to API and connect to WebSocket
    try:
        # Send message to REST API
        response = requests.post(f"{API_URL}/chats", json=message)
        if response.status_code == 200:
            st.session_state.messages.append(message)
            
                        # Connect to WebSocket for real-time updates
            async def connect_websocket():
                while True:
                    try:
                        uri = f"ws://localhost:8000/ws/{st.session_state.conversation_id}"
                        async with websockets.connect(uri) as websocket:
                            while True:
                                try:
                                    data = await websocket.recv()
                                    message_data = json.loads(data)
                                    st.session_state.messages.append(message_data['message'])
                                    if 'insights' in message_data:
                                        st.session_state.insights[message_data['message']['user_id']] = message_data['insights']
                                    st.rerun()
                                except websockets.exceptions.ConnectionClosed:
                                    break
                    except Exception as e:
                        await asyncio.sleep(1)  # Wait before retrying
                    
            # Run WebSocket connection in background thread
            def run_websocket():
                asyncio.run(connect_websocket())
            
            thread = threading.Thread(target=run_websocket, daemon=True)
            thread.start()
        else:
            st.error(f"Error sending message: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Display current conversation details
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Current Conversation ID:** {st.session_state.conversation_id}")
st.sidebar.markdown(f"**Messages in conversation:** {len(st.session_state.messages)}")