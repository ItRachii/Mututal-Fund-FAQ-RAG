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

# ChatGPT-like Minimalist Layout - Exact Match
st.markdown("""
<style>
    /* Dark Background #0F1116 */
    .stApp {
        background-color: #0F1116;
        color: #ececec;
    }
    
    /* Centering the container */
    .main-container {
        max-width: 720px;
        margin: 0 auto;
        padding-top: 10rem;
    }

    /* Hero Text */
    .hero-text {
        font-size: 2.8rem;
        font-weight: 500;
        text-align: center;
        margin-bottom: 3rem;
        color: #ffffff;
    }

    /* Input Bar Container styling (Both Home Search and Chat Bar) */
    .stChatInputContainer, .stTextInput > div > div > input {
        border-radius: 12px !important;
        background-color: #1A1D23 !important;
        border: 1px solid #30363D !important;
        color: #ececec !important;
        padding: 5px 15px !important;
    }

    /* Back Button Styling (Subtle Link) */
    div[data-testid="stButton"] button:has(div:contains("Back to Home")) {
        border: none !important;
        background-color: transparent !important;
        color: #8B949E !important;
        padding: 0 !important;
        font-size: 0.9rem !important;
        margin-top: -40px !important;
        margin-bottom: 20px !important;
    }
    div[data-testid="stButton"] button:has(div:contains("Back to Home")):hover {
        color: #ffffff !important;
        text-decoration: underline !important;
    }
    
    /* Remove padding/margins from text input wrapper */
    .stTextInput {
        padding: 0 !important;
    }
    
    /* Input placeholder styling */
    input::placeholder {
        color: #8B949E !important;
    }

    /* Suggestion Links (Simple Text) */
    .suggestion-container {
        max-width: 720px;
        margin: 0 auto;
        text-align: left;
        padding-left: 10px;
    }
    
    .stButton>button {
        border: none !important;
        background-color: transparent !important;
        color: #ececec !important;
        text-align: left !important;
        padding: 2px 0 !important;
        font-size: 1rem !important;
        font-weight: 400 !important;
        display: block !important;
        width: auto !important;
        box-shadow: none !important;
    }
    .stButton>button:hover {
        color: #3b82f6 !important; /* Subtle blue on hover */
        text-decoration: underline !important;
    }

    /* Subtle Footer Disclaimer */
    .fixed-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0F1116;
        color: #8B949E;
        text-align: center;
        padding: 20px;
        font-size: 13px;
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

# Interaction logic processing (Move to Top for Instant Response)
current_q = None
if st.session_state.user_query:
    current_q = st.session_state.user_query
    st.session_state.user_query = "" 
    st.session_state.messages.append({"role": "user", "content": current_q})

# Hero Section (Home Screen) - Only show if no messages AND no active query processing
if not st.session_state.messages and not current_q:
    with st.container():
        st.markdown('<div style="height: 15vh;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-text">What can I help with?</div>', unsafe_allow_html=True)
        
        _, col_mid, _ = st.columns([1, 4, 1])
        with col_mid:
            h_input = st.text_input("Home Search", label_visibility="collapsed", placeholder="Ask anything", key="home_input")
            
            st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
            st.markdown('<div style="color: #8B949E; font-size: 0.9rem; padding-left: 2px;">you may ask</div>', unsafe_allow_html=True)
            examples = [
                "What is the riskometer level for large cap?",
                "What are the top 5 holdings of HDFC Flexi Cap Fund?",
                "Tell me about ELSS lock-in period."
            ]
            for ex in examples:
                if st.button(ex, key=f"ex_{ex}"):
                    st.session_state.user_query = ex
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            if h_input:
                st.session_state.user_query = h_input
                st.rerun()

# Chat Layout (Active Conversation)
else:
    # Floating Back Button
    if st.button("← Back to Home", key="back_btn"):
        st.session_state.messages = []
        st.session_state.user_query = ""
        st.rerun()

    # Display chat messages from history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # If we are currently processing a brand new query (current_q), show assistant response
    if current_q:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                with st.spinner("Retrieving facts..."):
                    response = httpx.post(API_URL, json={"query": current_q}, timeout=60.0)
                    if response.status_code == 200:
                        answer = response.json().get("answer", "No response.")
                        message_placeholder.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        message_placeholder.error(f"Error: Backend returned {response.status_code}")
            except Exception as e:
                message_placeholder.error(f"Connection Error: {e}")

    # Bottom Fixed Input for active chat
    user_input = st.chat_input("Ask anything", key="chat_bar")
    if user_input:
        st.session_state.user_query = user_input
        st.rerun()

# Fixed Footer Disclaimer
st.markdown("""
<div class="fixed-footer">
    Facts-only assistant. No investment advice. Based on HDFC AMC documents.
</div>
""", unsafe_allow_html=True)
