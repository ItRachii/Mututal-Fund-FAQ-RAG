import streamlit as st
import httpx
import time

# Configuration
API_URL = "http://localhost:8000/chat"

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="HDFC MF Assistant",
    page_icon="🏦",
    layout="wide"
)

# ChatGPT-like Minimalist Layout with Previous Premium Theme
st.markdown("""
<style>
    /* Restore Light Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #1e293b;
    }
    
    /* Centering the container */
    .main-container {
        max-width: 800px;
        margin: 0 auto;
        padding-top: 5rem;
    }

    /* Hero Text */
    .hero-text {
        font-size: 2.5rem;
        font-weight: 600;
        text-align: center;
        margin-bottom: 2rem;
        border-top: none;
        color: #1e293b;
    }

    /* Suggestion Buttons (Premium Blue) */
    .stButton>button {
        border-radius: 12px;
        border: 1px solid #3b82f6;
        color: #3b82f6;
        background-color: rgba(255, 255, 255, 0.5);
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }

    /* Chat Input Styling */
    .stChatInputContainer {
        border-radius: 26px !important;
        background-color: white !important;
        border: 1px solid #e2e8f0 !important;
        padding: 5px 15px !important;
    }

    /* Subtle Footer Disclaimer */
    .fixed-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: #64748b;
        text-align: center;
        padding: 10px;
        font-size: 11px;
        z-index: 1000;
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# --- APP LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

# Hero Section (only shown if no messages)
if not st.session_state.messages:
    st.markdown('<div class="hero-text">What can I help with?</div>', unsafe_allow_html=True)
    
    # Grid of suggestions
    col1, col2 = st.columns(2)
    examples = [
        "What is the riskometer level for large cap?",
        "What are the top 10 holdings of HDFC Flexi Cap Fund?",
        "What is the exit load for HDFC Top 100?",
        "Tell me about ELSS lock-in period."
    ]
    
    with col1:
        if st.button(examples[0], use_container_width=True):
            st.session_state.user_query = examples[0]
            st.rerun()
        if st.button(examples[1], use_container_width=True):
            st.session_state.user_query = examples[1]
            st.rerun()
    with col2:
        if st.button(examples[2], use_container_width=True):
            st.session_state.user_query = examples[2]
            st.rerun()
        if st.button(examples[3], use_container_width=True):
            st.session_state.user_query = examples[3]
            st.rerun()

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle interaction
user_input = st.chat_input("Ask anything", key="user_query")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get Response from Backend
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            with st.spinner("Retrieving facts..."):
                response = httpx.post(API_URL, json={"query": user_input}, timeout=60.0)
                if response.status_code == 200:
                    answer = response.json().get("answer", "No response.")
                    message_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    err_msg = f"Error: Backend returned {response.status_code}"
                    message_placeholder.error(err_msg)
        except Exception as e:
            err_msg = f"Connection Error: {e}"
            message_placeholder.error(err_msg)

# Fixed Footer Disclaimer
st.markdown("""
<div class="fixed-footer">
    Facts-only assistant. No investment advice. Based on HDFC AMC documents.
</div>
""", unsafe_allow_html=True)
