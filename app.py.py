import streamlit as st
import json
import random
import time
import base64

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
    """Encodes the current game state into a base64 string"""
    state_data = {
        'current_index': st.session_state.current_index,
        'score': st.session_state.score,
        'quiz_data': st.session_state.quiz_data, # Saves the specific shuffled order
    }
    json_str = json.dumps(state_data)
    b64_str = base64.b64encode(json_str.encode()).decode()
    return b64_str

def load_save_code(code):
    """Decodes a save string and restores the game"""
    try:
        json_str = base64.b64decode(code).decode()
        state_data = json.loads(json_str)
        
        st.session_state.current_index = state_data['current_index']
        st.session_state.score = state_data['score']
        st.session_state.quiz_data = state_data['quiz_data']
        st.session_state.game_active = True
        st.session_state.quiz_finished = False
        st.session_state.answer_submitted = False
        return True
    except:
        return False

# --- Initialization ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False

raw_questions = load_questions()

# ==========================================
# SCREEN 1: THE START MENU (HOME)
# ==========================================
if not st.session_state.game_active and not st.session_state.quiz_finished:
    st.title("🎓 Exam Simulator Pro")
    st.markdown("Welcome! Configure your session below.")

    with st.expander("⚙️ Settings & Learning Options", expanded=True):
        st.write("Customize your learning experience:")
        
        # Setting: Shuffle
        shuffle_opt = st.checkbox("Randomize Question Order", value=True, help="If checked, questions will appear in a random order every time.")
        
        # Setting: Question Limit
        max_qs = len(raw_questions)
        q_limit = st.slider("Number of Questions to Study", min_value=1, max_value=max_qs, value=max_qs)
        
        st.info("💡 **Tip:** Try doing small batches of 10-20 questions to improve retention!")

    col1, col2 = st.columns(2)
    
    # START BUTTON
    with col1:
        if st.button("▶️ Start New Exam", type="primary", use_container_width=True):
            # Loading Effect
            with st.spinner("Shuffling questions and preparing exam..."):
                time.sleep(1.5) # Fake loading for effect
            
            # Setup Game State
            subset_questions = raw_questions[:] # Copy list
            if shuffle_opt:
                random.shuffle(subset_questions)
            
            # Trim to limit
            st.session_state.quiz_data = subset_questions[:q_limit]
            
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.answer_submitted = False
            st.session_state.game_active = True
            st.rerun()

    # LOAD BUTTON
    with col2:
        with st.popover("📂 Load Saved Game"):
            save_code_input = st.text_input("Paste your Save Code here:")
            if st.button("Resume Game"):
                if load_save_code(save_code_input):
                    st.success("Game Loaded!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Save Code.")

# ==========================================
# SCREEN 2: THE GAME
# ==========================================
elif st.session_state.game_active and not st.session_state.quiz_finished:
    
    # --- Sidebar: Save & Quit ---
    with st.sidebar:
        st.header("⏸ Options")
        st.write("Need to take a break? Get a code to resume later.")
        if st.button("💾 Get Save Code"):
            code = generate_save_code()
            st.code(code, language=None)
            st.warning("Copy this code! You will need it to resume if you close the browser.")
            
        if st.button("❌ Quit to Menu"):
            st.session_state.game_active = False
            st.rerun()

    # --- Metrics & Progress ---
    questions = st.session_state.quiz_data
    total_qs = len(questions)
    current_idx = st.session_state.current_index
    
    # Calculate accuracy
    qs_answered = current_idx + (1 if st.session_state.answer_submitted else 0)
    current_accuracy = (st.session_state.score / qs_answered) if qs_answered > 0 else 0.0

    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"Question {current_idx + 1} of {total_qs}")
        st.progress((current_idx + 1) / total_qs)
    with c2:
        st.caption(f"Accuracy: {current_accuracy:.0%}")
        if current_accuracy > 0.7:
            st.progress(current_accuracy) # Blue/Green default
        else:
            st.progress(current_accuracy) # Would need custom CSS for red, but default is fine

    # --- Question Display ---
    q = questions[current_idx]
    st.subheader(f"{q['question_text']}")
    
    # Options
    options = q['options']
    choice_labels = [f"{key}: {value}" for key, value in sorted(options.items())]
    
    # Radio Button
    user_choice = st.radio(
        "Select your answer:", 
        choice_labels, 
        key=f"q_{current_idx}", 
        disabled=st.session_state.answer_submitted,
        index=None # No default selection
    )

    # --- Buttons (Submit / Next) ---
    col_submit, col_empty = st.columns([1, 4])
    
    if not st.session_state.answer_submitted:
        with col_submit:
            if st.button("Submit Answer", type="primary"):
                if user_choice:
                    st.session_state.answer_submitted = True
                    st.rerun()
                else:
                    st.warning("Please select an option.")
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
            st.error(f"❌ Incorrect. The answer was {correct_key}.")
            
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
    
    st.metric("Final Score", f"{final_score} / {total}", f"{percent:.1f}%")
    
    if percent >= 70:
        st.success("You passed! Excellent work.")
    else:
        st.warning("Good effort. Review your weak spots and try again!")
        
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Return to Home Screen"):
            st.session_state.quiz_finished = False
            st.session_state.game_active = False
            st.rerun()
    with col2:
        if st.button("🔄 Play Again (Same Questions)"):
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.quiz_finished = False
            st.session_state.game_active = True
            st.rerun()
