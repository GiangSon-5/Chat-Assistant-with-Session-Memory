import streamlit as st
import sys
import json
import logging
from pathlib import Path
from datetime import datetime  # <--- [NEW] Import datetime

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import Config
from src.llm_client import LLMClient
from src.session_memory import SessionMemoryManager
from src.query_processor import QueryProcessor
from src.token_counter import TokenCounter
from src.storage import StorageManager

# Logging Setup
logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="AI Backend Architect Demo", layout="wide")

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "demo_session_01"
if "pipeline_logs" not in st.session_state:
    st.session_state.pipeline_logs = []

# --- Sidebar Config ---
st.sidebar.title("⚙️ System Config")
api_url = st.sidebar.text_input("LLM API URL (ngrok)", value=Config.LLM_API_BASE_URL)
Config.LLM_API_BASE_URL = api_url 

# [NEW] Dynamic Session ID Input
custom_session_id = st.sidebar.text_input("Session ID", value=st.session_state.session_id)

# Logic: Nếu người dùng đổi tên Session ID -> Reset lại bộ nhớ và tin nhắn hiển thị
if custom_session_id != st.session_state.session_id:
    st.session_state.session_id = custom_session_id
    st.session_state.messages = [] # Xóa chat trên màn hình để bắt đầu mới
    st.session_state.pipeline_logs = []
    st.rerun() # Load lại trang để áp dụng ID mới

threshold = st.sidebar.slider("Memory Threshold (Tokens)", 100, 5000, 200)

# Initialize Components
llm_client = LLMClient(base_url=api_url)
# Memory Manager sẽ khởi tạo theo Session ID hiện tại
memory_manager = SessionMemoryManager(st.session_state.session_id, llm_client)
query_processor = QueryProcessor(llm_client)
token_counter = TokenCounter()

# --- CSS Styling (Fix Dark Mode/Light Mode) ---
st.markdown(
    """
    <style>
    /* Sticky Header Config */
    .sticky-header {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 999;
        padding: 0.75rem 1rem;
        backdrop-filter: blur(8px);
        border-bottom: 1px solid rgba(0,0,0,0.08);
        transition: background-color 0.3s ease, color 0.3s ease;
    }

    .sticky-header h1 { 
        margin: 0; 
        font-size: 1.6rem; 
        font-weight: 700;
    }
    
    .sticky-header p { 
        margin: 0; 
        font-size: 0.9rem;
    }

    /* Light Mode (Default) */
    .sticky-header {
        background: rgba(255, 255, 255, 0.90);
        color: #31333F;
    }
    .sticky-header p {
        color: #6c6f73;
    }

    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        .sticky-header {
            background: rgba(14, 17, 23, 0.90);
            color: #FAFAFA;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .sticky-header h1 {
            color: #FAFAFA;
        }
        .sticky-header p {
            color: #BCBCBC !important;
        }
    }

    .stApp .block-container { 
        padding-top: 4.5rem; 
    }
    </style>
    <div class="sticky-header">
      <h1>🧠 Chat Assistant with Session Memory</h1>
      <p><strong>Auto-Summarization</strong> &amp; <strong>Query Understanding Pipeline</strong>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "💬 Chat Interface"
selected_tab = st.sidebar.radio(
    "View",
    ("💬 Chat Interface", "💾 Memory & State", "🛠️ Pipeline Visualizer"),
    index=["💬 Chat Interface", "💾 Memory & State", "🛠️ Pipeline Visualizer"].index(st.session_state.selected_tab),
    key="selected_tab",
)

# --- Sidebar Test triggers ---
with st.sidebar:
    st.divider()
    if st.button("Load Long Conversation (Trigger Memory)"):
        data = StorageManager.load_test_data("long_conversation.jsonl")
        if data:
            st.session_state.messages = [d["message"] for d in data]
            st.toast(f"Loaded {len(data)} messages!", icon="✅")
            summary = memory_manager.check_and_summarize(st.session_state.messages, threshold)
            if summary:
                st.session_state.pipeline_logs.append({"step": "Memory Triggered", "details": summary.model_dump()})

# --- Chat Logic ---
if selected_tab == "💬 Chat Interface":
    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Show caption if it was a clarification request
            if msg.get("is_clarification", False):
                st.caption("💡 *This was a clarification request from AI*")

    # Handle User Input
    if prompt := st.chat_input("Type your query..."):
        # [NEW] Capture Current Time
        current_time = datetime.now().isoformat()
        
        # 1. Display user message first
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Pipeline Execution
        with st.status("Processing Pipeline...", expanded=True) as status:
            
            # Step A: Check Memory
            st.write("Checking Context Size...")
            summary = memory_manager.check_and_summarize(st.session_state.messages, threshold)
            if summary:
                st.write("⚠️ Threshold exceeded! Summarizing history...")

            # Step B: Query Understanding
            st.write("Analyzing Query Ambiguity...")
            memory_context = memory_manager.get_context_string()
            
            # Process query with history (excluding current prompt yet)
            analysis = query_processor.process_query(
                query=prompt, 
                recent_history=st.session_state.messages, 
                memory_context=memory_context
            )

            # --- [CRITICAL LOGIC] OVERRIDE CONFIDENCE SCORE ---
            if analysis.is_ambiguous and analysis.confidence_score < 0.9:
                analysis.requires_clarification = True
                if not analysis.clarifying_questions:
                    analysis.clarifying_questions = [
                        f"I'm not 100% sure what '{prompt}' refers to in this context. Could you clarify?",
                        f"Are you asking about {analysis.rewritten_query}?"
                    ]

            st.session_state.pipeline_logs.append(
                {"step": "Query Analysis", "details": analysis.model_dump()}
            )

            # Initialize flow variables
            is_clarification = False
            response_text = ""

            # --- BRANCHING LOGIC ---
            if analysis.requires_clarification:
                # [PATH 1: STOP & ASK]
                st.write(f"🛑 Ambiguous request (Confidence: {analysis.confidence_score}). Asking for clarification...")
                
                clarification_msg = analysis.clarifying_questions[0] if analysis.clarifying_questions else "Could you please clarify?"
                
                response_text = clarification_msg
                is_clarification = True
                status.update(label="Clarification Needed", state="complete", expanded=False)

            else:
                # [PATH 2: GENERATE ANSWER]
                st.write(f"✅ Query is clear (Confidence: {analysis.confidence_score}).")
                if analysis.is_ambiguous:
                    st.write(f"🔄 Rewritten: **{analysis.rewritten_query}**")
                
                st.write("Generating Response...")

                context_to_use = analysis.augmented_context
                if not context_to_use:
                    context_to_use = "No specific context found."

                # Get User Profile for Personalization
                user_profile_str = ""
                if memory_manager.current_memory:
                     user_profile_str = f"User Profile/Facts: {memory_manager.current_memory.session_summary.key_facts}"

                final_system_prompt = f"""
                You are a helpful AI assistant.
                Current Date: {datetime.now().strftime("%Y-%m-%d")}
                
                === USER INFORMATION ===
                {user_profile_str}
                
                === CONTEXT ===
                {context_to_use}
                
                INSTRUCTIONS:
                - Answer the user's question using the CONTEXT.
                - Maintain a helpful tone.
                """
                
                # [FIX CONTEXT LOSS] Use sliding window of last 15 messages
                recent_msgs_for_context = st.session_state.messages[-15:] 
                
                final_messages = [{"role": "system", "content": final_system_prompt}]
                
                # Append Clean History
                for m in recent_msgs_for_context:
                    clean_msg = {"role": m["role"], "content": m["content"]}
                    final_messages.append(clean_msg)
                
                # Append Rewritten Query
                final_messages.append({"role": "user", "content": analysis.rewritten_query})

                response_text = llm_client.chat_completion(final_messages)
                status.update(label="Complete!", state="complete", expanded=False)

        # 3. Output & Update State
        # [NEW] Save timestamp to session history
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "timestamp": current_time
        })
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response_text,
            "is_clarification": is_clarification,
            "timestamp": datetime.now().isoformat()
        })
        
        with st.chat_message("assistant"):
            st.markdown(response_text)
            if is_clarification:
                st.info("💡 I need a bit more detail to answer accurately.")

# --- Tab: Memory View ---
if selected_tab == "💾 Memory & State":
    st.subheader(f"Current Session Summary: {st.session_state.session_id}")
    if memory_manager.current_memory:
        st.json(memory_manager.current_memory.model_dump())
    else:
        st.info("No summary generated yet.")

# --- Tab: Pipeline Debug ---
if selected_tab == "🛠️ Pipeline Visualizer":
    st.subheader("Pipeline Logs")
    for log in reversed(st.session_state.pipeline_logs):
        with st.expander(f"{log['step']}"):
            st.json(log["details"])