import streamlit as st
import requests
import json
from datetime import datetime
import asyncio
from collections import defaultdict
import time
import aiohttp

# Page config must be first
st.set_page_config(page_title="Chat Demo", layout="wide")
st.title("Chat Demo")

# Configure the API URL
API_URL = "http://localhost:8000"

# Configure request debouncing
DEBOUNCE_TIME = 0.2

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    # Load existing messages from backend when initializing
    async def load_messages():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/chats/{st.session_state.conversation_id}") as response:
                    if response.status == 200:
                        messages = await response.json()
                        st.session_state.messages = messages
        except Exception as e:
            st.error(f"Error loading messages: {str(e)}")
    
    asyncio.run(load_messages())

if 'message_cache' not in st.session_state:
    st.session_state.message_cache = {}
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user"
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0
if 'filtered_messages' not in st.session_state:
    st.session_state.filtered_messages = []
if 'last_message_count' not in st.session_state:
    st.session_state.last_message_count = 0

# Sidebar with restored functionality
with st.sidebar:
    st.header("Chat Settings")
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
    st.session_state.conversation_id = st.text_input("Conversation ID", value=st.session_state.conversation_id)
    
    if st.button("New Conversation"):
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []
        st.session_state.filtered_messages = []
        st.rerun()
    
    # Restored Search and Filter Section
    st.header("Search & Filter")
    search_query = st.text_input("Search messages", key="search_input")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", None)
    with col2:
        end_date = st.date_input("To", None)
    
    if st.button("Apply Filters"):
        filtered_messages = st.session_state.messages
        if search_query:
            filtered_messages = [
                msg for msg in filtered_messages
                if search_query.lower() in msg["message"].lower()
            ]
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            filtered_messages = [
                msg for msg in filtered_messages
                if datetime.fromisoformat(msg["timestamp"]) >= start_datetime
            ]
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            filtered_messages = [
                msg for msg in filtered_messages
                if datetime.fromisoformat(msg["timestamp"]) <= end_datetime
            ]
        
        st.session_state.filtered_messages = filtered_messages
    
    # Restored Analysis Options
    st.header("Analysis Options")
    include_sentiment = st.checkbox("Include Sentiment Analysis")
    include_keywords = st.checkbox("Include Keyword Extraction")
    
    if st.button("Generate Summary") and st.session_state.messages:
        with st.spinner("Generating summary..."):
            try:
                async def generate_summary_async():
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{API_URL}/chats/summarize",
                            json={
                                "conversation_id": st.session_state.conversation_id,
                                "include_sentiment": include_sentiment,
                                "include_keywords": include_keywords
                            }
                        ) as response:
                            if response.status == 200:
                                return await response.json()
                            else:
                                st.error(f"Error: {await response.text()}")
                                return None
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                summary = loop.run_until_complete(generate_summary_async())
                
                if summary:
                    st.success("Summary generated!")
                    st.text_area("Summary", summary.get("summary", ""), height=150)
                    if include_sentiment and "sentiment" in summary:
                        st.info(f"Sentiment: {summary['sentiment']}")
                    if include_keywords and "keywords" in summary:
                        st.info(f"Keywords: {', '.join(summary['keywords'])}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Main chat interface
st.write("### Chat Messages")
chat_container = st.empty()  # Use empty container for efficient updates

# Function to update chat display efficiently
def update_chat_display():
    with chat_container.container():
        messages_to_display = st.session_state.filtered_messages if st.session_state.filtered_messages else st.session_state.messages
        for msg in messages_to_display:
            with st.chat_message("user" if msg["user_id"] == st.session_state.user_id else "assistant"):
                st.write(msg["message"])

# Initial display
update_chat_display()

# Chat input at the bottom
# Async function to send messages
async def send_message_async(message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{API_URL}/chats", json=message) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    st.error(f"Error sending message: {await response.text()}")
                    return None
    except Exception as e:
        st.error(f"Network error: {str(e)}")
        return None

# Handle chat input
if prompt := st.chat_input("Type your message here"):
    current_time = time.time()
    if current_time - st.session_state.last_request_time < DEBOUNCE_TIME:
        st.warning("Please wait a moment before sending another message...")
    else:
        st.session_state.last_request_time = current_time
        message = {
            "conversation_id": st.session_state.conversation_id,
            "user_id": st.session_state.user_id,
            "message": prompt,
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }
        st.session_state.messages.append(message)
        update_chat_display()
        message_id = f"{st.session_state.conversation_id}_{len(st.session_state.messages)}"
        st.session_state.message_cache[message_id] = message
        
        async def process_message():
            bot_response = await send_message_async(message)
            if bot_response:
                st.session_state.messages.append(bot_response)
                if message_id in st.session_state.message_cache:
                    del st.session_state.message_cache[message_id]
                update_chat_display()
        
        asyncio.run(process_message())

# Status information
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Conversation ID:** {st.session_state.conversation_id}")
st.sidebar.markdown(f"**Total Messages:** {len(st.session_state.messages)}")
if st.session_state.filtered_messages:
    st.sidebar.markdown(f"**Filtered Messages:** {len(st.session_state.filtered_messages)}")