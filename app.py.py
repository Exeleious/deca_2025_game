
import streamlit as st
import json
import random
import time
import base64
import pandas as pd
from datetime import datetime

# --- Helper Functions ---

@st.cache_data
def load_questions():
    try:
        with open('exam_formatted_game.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: 'exam_formatted_game.json' not found.")
        return []

def generate_save_code():
    """Encodes the current game state AND history into a base64 string"""
    state_data = {
        'current_index': st.session_state.current_index,
        'score': st.session_state.score,
        'quiz_data': st.session_state.quiz_data,
        'history': st.session_state.history, # SAVES YOUR LEADERBOARD!
        'incorrect_indices': st.session_state.incorrect_indices
    }
    json_str = json.dumps(state_data, default=str)
    b64_str = base64.b64encode(json_str.encode()).decode()
    return b64_str

def load_save_code(code):
    """Decodes a save string and restores the game and history"""
    try:
        json_str = base64.b64decode(code).decode()
        state_data = json.loads(json_str)
        
        st.session_state.current_index = state_data.get('current_index', 0)
        st.session_state.score = state_data.get('score', 0)
        st.session_state.quiz_data = state_data.get('quiz_data', [])
        st.session_state.history = state_data.get('history', [])
        st.session_state.incorrect_indices = state_data.get('incorrect_indices', [])
        
        st.session_state.game_active = True
        st.session_state.quiz_finished = False
        st.session_state.answer_submitted = False
        return True
    except Exception as e:
        return False

# --- Initialization ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False
if 'history' not in st.session_state:
    st.session_state.history = [] # Stores past exam results
if 'incorrect_indices' not in st.session_state:
    st.session_state.incorrect_indices = [] # Tracks wrong answers in current session

raw_questions = load_questions()

# ==========================================
# SCREEN 1: THE START MENU (HOME)
# ==========================================
if not st.session_state.game_active and not st.session_state.quiz_finished:
    st.title("🎓 Exam Simulator Pro")
    st.markdown("Welcome back! Ready to master the material?")

    # --- LEADERBOARD / HISTORY SECTION ---
    if st.session_state.history:
        with st.expander("🏆 Your Progress (Leaderboard)", expanded=False):
            # Convert history to DataFrame for nice display
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df, use_container_width=True)
            
            # Simple line chart of scores
            if len(df) > 1:
                st.line_chart(df.set_index("Date")["Score (%)"])
            
            avg_score = df["Score (%)"].mean()
            st.metric("Average Performance", f"{avg_score:.1f}%")

    with st.container(border=True):
        st.subheader("⚙️ Settings")
        
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            shuffle_opt = st.checkbox("Randomize Order", value=True)
        with col_set2:
            max_qs = len(raw_questions)
            q_limit = st.slider("Question Count", 1, max_qs, min(10, max_qs))

    col1, col2 = st.columns(2)
    
    # START BUTTON
    with col1:
        if st.button("▶️ Start New Exam", type="primary", use_container_width=True):
            with st.spinner("Preparing exam..."):
                time.sleep(1)
            
            # Setup Game State
            subset_questions = raw_questions[:] 
            if shuffle_opt:
                random.shuffle(subset_questions)
            
            st.session_state.quiz_data = subset_questions[:q_limit]
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.incorrect_indices = [] # Reset wrong answers
            st.session_state.answer_submitted = False
            st.session_state.game_active = True
            st.rerun()

    # LOAD BUTTON
    with col2:
        with st.popover("📂 Load Saved Game"):
            save_code_input = st.text_input("Paste Save Code:")
            if st.button("Resume"):
                if load_save_code(save_code_input):
                    st.success("Loaded!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Code.")

# ==========================================
# SCREEN 2: THE GAME
# ==========================================
elif st.session_state.game_active and not st.session_state.quiz_finished:
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("⏸ Menu")
        if st.button("💾 Save Progress"):
            code = generate_save_code()
            st.code(code, language=None)
            st.warning("Copy this code to save your history and current spot!")
            
        if st.button("❌ Quit to Menu"):
            st.session_state.game_active = False
            st.rerun()

    # --- Metrics ---
    questions = st.session_state.quiz_data
    total_qs = len(questions)
    current_idx = st.session_state.current_index
    
    # Accuracy Logic
    qs_answered = current_idx + (1 if st.session_state.answer_submitted else 0)
    current_accuracy = (st.session_state.score / qs_answered) if qs_answered > 0 else 0.0

    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"Question {current_idx + 1} of {total_qs}")
        st.progress((current_idx + 1) / total_qs)
    with c2:
        st.caption(f"Accuracy: {current_accuracy:.0%}")
        st.progress(current_accuracy)

    # --- Question Display ---
    q = questions[current_idx]
    st.subheader(f"{q['question_text']}")
    
    options = q['options']
    choice_labels = [f"{key}: {value}" for key, value in sorted(options.items())]
    
    # Radio Button
    user_choice = st.radio(
        "Select Answer:", 
        choice_labels, 
        key=f"q_{current_idx}", 
        disabled=st.session_state.answer_submitted,
        index=None
    )

    # --- Interaction Logic ---
    col_submit, col_empty = st.columns([1, 4])
    
    if not st.session_state.answer_submitted:
        with col_submit:
            if st.button("Submit Answer", type="primary"):
                if user_choice:
                    st.session_state.answer_submitted = True
                    st.rerun()
                else:
                    st.toast("Please select an option first!", icon="⚠️")
    else:
        # Check Answer
        selected_key = user_choice.split(":")[0]
        correct_key = q['answer_key']
        
        if selected_key == correct_key:
            st.success("✅ Correct!")
            if "scored_current" not in st.session_state:
                st.session_state.score += 1
                st.session_state.scored_current = True
        else:
            st.error(f"❌ Incorrect. Answer: {correct_key}")
            # Track this wrong question for later!
            if "scored_current" not in st.session_state:
                st.session_state.incorrect_indices.append(q) 
                st.session_state.scored_current = True
            
        st.info(f"**Rationale:** {q['rationale']}")
        
        if st.button("Next Question ➡"):
            st.session_state.answer_submitted = False
            if "scored_current" in st.session_state:
                del st.session_state.scored_current
            
            if current_idx + 1 < total_qs:
                st.session_state.current_index += 1
            else:
                st.session_state.quiz_finished = True
                st.session_state.game_active = False
            st.rerun()

# ==========================================
# SCREEN 3: GAME OVER
# ==========================================
elif st.session_state.quiz_finished:
    st.balloons()
    st.title("🎉 Session Complete!")
    
    final_score = st.session_state.score
    total = len(st.session_state.quiz_data)
    percent = (final_score / total) * 100
    
    # Save to History (if not already saved for this run)
    if "history_saved" not in st.session_state:
        st.session_state.history.append({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Score": f"{final_score}/{total}",
            "Score (%)": round(percent, 1)
        })
        st.session_state.history_saved = True

    st.metric("Final Score", f"{final_score} / {total}", f"{percent:.1f}%")
    
    st.write("---")
    
    col1, col2, col3 = st.columns(3)
    
    # Button 1: Home
    with col1:
        if st.button("🏠 Home Screen"):
            if "history_saved" in st.session_state:
                del st.session_state.history_saved
            st.session_state.quiz_finished = False
            st.session_state.game_active = False
            st.rerun()

    # Button 2: Retry Missed (The New Feature!)
    with col2:
        missed_qs = st.session_state.incorrect_indices
        if len(missed_qs) > 0:
            if st.button(f"🔁 Retry {len(missed_qs)} Missed"):
                if "history_saved" in st.session_state:
                    del st.session_state.history_saved
                
                # Load only the missed questions
                st.session_state.quiz_data = missed_qs[:]
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.incorrect_indices = []
                st.session_state.quiz_finished = False
                st.session_state.game_active = True
                st.rerun()
        else:
            st.button("🔁 Retry Missed", disabled=True, help="You got everything right!")

    # Button 3: Play Again
    with col3:
        if st.button("🔄 New Exam"):
            if "history_saved" in st.session_state:
                del st.session_state.history_saved
            # Reset completely
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.incorrect_indices = []
            st.session_state.quiz_finished = False
            st.session_state.game_active = False # Go back to setup to reshuffle
            st.rerun()
