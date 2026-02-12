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

    /* Pill-Shaped Input Bar Container styling (Both Home Search and Chat Bar) */
    .stChatInputContainer {
        padding: 0 !important;
        background-color: #0F1116 !important; /* Match app background */
        border: none !important;
    }

    .stChatInputContainer > div, .stTextInput > div > div {
        border-radius: 50px !important;
        background-color: #2F2F2F !important; /* Lighter gray like the image */
        border: none !important;
        overflow: hidden !important;
        padding: 0 20px !important;
    }
    
    /* Make the inner input transparent and borderless */
    .stChatInputContainer textarea, .stTextInput input {
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        color: #ececec !important;
        padding: 12px 15px !important;
        font-size: 1.1rem !important;
    }
    
    /* Remove padding/margins from text input wrapper */
    .stTextInput {
        padding: 0 !important;
    }
    
    /* Input placeholder styling */
    input::placeholder, textarea::placeholder {
        color: #8E8E8E !important;
    }

    /* Fixed Back Button Styling */
    .fixed-back-btn {
        position: fixed;
        top: 24px;
        left: 24px;
        z-index: 999999;
    }

    .fixed-back-btn button {
        background: transparent;
        color: #8B949E;
        border: none;
        font-size: 16px;
        cursor: pointer;
        padding: 6px 10px;
    }

    .fixed-back-btn button:hover {
        color: white;
    }
    
    /* Suggestion Links (Simple Text) */
    .suggestion-container {
        max-width: 720px;
        margin: 0 auto;
        text-align: left;
        padding: 10px 0 0 25px; /* Indent to match input text start */
    }
    
    .stButton>button {
        border: none !important;
        background-color: transparent !important;
        color: #ececec !important;
        text-align: left !important;
        padding: 4px 0 !important;
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

    /* Bouncing Dots Animation */
    .typing-dots {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 10px 0;
    }
    .dot {
        width: 8px;
        height: 8px;
        background-color: #8B949E;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1.0); }
    }

    /* Input placeholder styling - Make it look like active text during processing */
    input::placeholder {
        color: #ececec !important; /* Brighter during processing */
        opacity: 0.8 !important;
    }

    /* Chat Message Alignment */
    /* Shared styles for both */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        width: fit-content !important;
        max-width: 85% !important;
        margin-bottom: 1rem !important;
    }
    
    div[data-testid="stChatMessage"] .stMarkdown {
        background-color: #2F2F2F !important;
        padding: 10px 20px !important;
        border-radius: 20px !important;
        display: inline-block !important;
    }

    /* User Message - Right Aligned */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) {
        flex-direction: row-reverse !important;
        margin-left: auto !important;
        text-align: right !important;
    }
    
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) section[data-testid="stChatMessageContent"] {
        margin-right: 12px !important;
        margin-left: 0 !important;
    }

    /* Assistant Message - Left Aligned */
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) {
        flex-direction: row !important;
        margin-right: auto !important;
        text-align: left !important;
    }

    /* Typing Dots Alignment - Left Aligned */
    .typing-dots {
        justify-content: flex-start !important;
        width: 100% !important;
    }

    /* Subtle Footer Disclaimer */
    .fixed-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0F1116;
        color: #676767;
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

if "back_home" not in st.session_state:
    st.session_state.back_home = False

# Handle Streamlit-safe Back to Home (Python Handler)
if st.session_state.get("back_home") or st.query_params.get("back_home"):
    st.session_state.messages = []
    st.session_state.user_query = ""
    st.session_state.back_home = False
    # Clear query params if present
    st.query_params.clear()
    st.rerun()

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
    # Inject True Fixed HTML Button (Bypasses Streamlit's internal scroller)
    st.markdown("""
    <div class="fixed-back-btn">
        <form action="/" method="get">
            <input type="hidden" name="back_home" value="true">
            <button type="submit">← Back to Home</button>
        </form>
    </div>
    """, unsafe_allow_html=True)

    # Display chat messages from history
    chat_container = st.container()
    with chat_container:
        # Dynamic Spacer to start chat from bottom
        msg_count = len(st.session_state.messages)
        spacer_height = max(10, 60 - (msg_count * 10))
        st.markdown(f'<div style="height: {spacer_height}vh;"></div>', unsafe_allow_html=True)

        for message in st.session_state.messages:
            # Use custom icons for both
            if message["role"] == "user":
                avatar = "src/frontend/assets/user_icon.svg"
            else:
                avatar = "src/frontend/assets/bot_icon.svg"
            
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # If we are currently processing a brand new query (current_q), show assistant response
    if current_q:
        # The user query is already in messages, so it's shown above in the loop
        with st.chat_message("assistant", avatar="src/frontend/assets/bot_icon.svg"):
            message_placeholder = st.empty()
            # Thinking animation: Bouncing dots
            message_placeholder.markdown("""
                <div class="typing-dots">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            """, unsafe_allow_html=True)
            
            try:
                # Backend call
                response = httpx.post(API_URL, json={"query": current_q}, timeout=60.0)
                if response.status_code == 200:
                    answer = response.json().get("answer", "No response.")
                    message_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    # Rerun once to stabilize state after answer
                    st.rerun()
                else:
                    message_placeholder.error(f"Error: Backend returned {response.status_code}")
            except Exception as e:
                message_placeholder.error(f"Connection Error: {e}")

    # Bottom Fixed Input for active chat
    input_placeholder = current_q if current_q else "Ask anything"
    user_input = st.chat_input(input_placeholder, key="chat_bar")
    if user_input:
        st.session_state.user_query = user_input
        st.rerun()

# Fixed Footer Disclaimer
st.markdown("""
<div class="fixed-footer">
    Facts-only assistant. No investment advice. Based on HDFC AMC documents.
</div>
""", unsafe_allow_html=True)
