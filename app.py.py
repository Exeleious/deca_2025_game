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
    # Update this filename if you change the JSON file name again!
    try:
        with open('exam_formatted_game', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: 'exam_formatted_game' not found.")
        return []

def generate_save_code():
    """Encodes the current game state AND history into a base64 string"""
    state_data = {
        'current_index': st.session_state.current_index,
        'score': st.session_state.score,
        'quiz_data': st.session_state.quiz_data,
        'history': st.session_state.history, 
        'incorrect_indices': st.session_state.incorrect_indices,
        'simulation_mode': st.session_state.simulation_mode,
        'user_answers': st.session_state.user_answers
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
        st.session_state.simulation_mode = state_data.get('simulation_mode', False)
        st.session_state.user_answers = state_data.get('user_answers', [])
        
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
    st.session_state.history = [] 
if 'incorrect_indices' not in st.session_state:
    st.session_state.incorrect_indices = [] 
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []

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
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df, use_container_width=True)
            
            if len(df) > 1:
                st.line_chart(df.set_index("Date")["Score (%)"])
            
            avg_score = df["Score (%)"].mean()
            st.metric("Average Performance", f"{avg_score:.1f}%")

    with st.container(border=True):
        st.subheader("⚙️ Settings")
        
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            shuffle_opt = st.checkbox("Randomize Order", value=True)
            sim_mode = st.checkbox("DECA Simulation Mode", value=False, help="No immediate feedback. Review all answers at the end of the exam.")
       with col_set2:
            max_qs = len(raw_questions)
            if max_qs == 0:
                st.warning("No questions found. Please check your JSON file.")
                st.stop() # This safely stops the app from crashing the slider!
            
            q_limit = st.slider("Question Count", 1, max_qs, min(100, max_qs))
    col1, col2 = st.columns(2)
    
    # START BUTTON
    with col1:
        if st.button("▶️ Start New Exam", type="primary", use_container_width=True):
            if len(raw_questions) > 0:
                with st.spinner("Preparing exam..."):
                    time.sleep(1)
                
                # Setup Game State
                subset_questions = raw_questions[:] 
                if shuffle_opt:
                    random.shuffle(subset_questions)
                
                st.session_state.quiz_data = subset_questions[:q_limit]
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.incorrect_indices = []
                st.session_state.user_answers = [] 
                st.session_state.answer_submitted = False
                st.session_state.simulation_mode = sim_mode
                if "sim_scored" in st.session_state:
                    del st.session_state.sim_scored
                
                st.session_state.game_active = True
                st.rerun()
            else:
                st.error("No questions loaded. Check your JSON file.")

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
    
    c1, c2 = st.columns([3, 1])
    with c1:
        st.caption(f"Question {current_idx + 1} of {total_qs}")
        st.progress((current_idx + 1) / total_qs)
    with c2:
        if st.session_state.simulation_mode:
            st.caption("Mode: 🛑 DECA Simulation")
        else:
            qs_answered = current_idx + (1 if st.session_state.answer_submitted else 0)
            current_accuracy = (st.session_state.score / qs_answered) if qs_answered > 0 else 0.0
            st.caption(f"Accuracy: {current_accuracy:.0%}")
            st.progress(current_accuracy)

    # --- Question Display ---
    q = questions[current_idx]
    st.subheader(f"{q['question_text']}")
    
    options = q['options']
    choice_labels = [f"{key}: {value}" for key, value in sorted(options.items())]
    
    # Check if we already answered this in simulation mode (for going back/forth, though we only move forward currently)
    pre_selected = None
    if st.session_state.simulation_mode and current_idx < len(st.session_state.user_answers):
        pre_idx = list(sorted(options.keys())).index(st.session_state.user_answers[current_idx])
        pre_selected = pre_idx

    user_choice = st.radio(
        "Select Answer:", 
        choice_labels, 
        key=f"q_{current_idx}", 
        disabled=st.session_state.answer_submitted,
        index=pre_selected
    )

    # --- Interaction Logic ---
    col_submit, col_empty = st.columns([1, 4])
    
    # ---- STUDY MODE LOGIC ----
    if not st.session_state.simulation_mode:
        if not st.session_state.answer_submitted:
            with col_submit:
                if st.button("Submit Answer", type="primary"):
                    if user_choice:
                        st.session_state.answer_submitted = True
                        st.rerun()
                    else:
                        st.toast("Please select an option first!", icon="⚠️")
        else:
            selected_key = user_choice.split(":")[0]
            correct_key = q['answer_key']
            
            if selected_key == correct_key:
                st.success("✅ Correct!")
                if "scored_current" not in st.session_state:
                    st.session_state.score += 1
                    st.session_state.scored_current = True
            else:
                st.error(f"❌ Incorrect. Answer: {correct_key}")
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

    # ---- SIMULATION MODE LOGIC ----
    else:
        with col_submit:
            button_text = "Next Question ➡" if current_idx + 1 < total_qs else "Finish Exam 🏁"
            if st.button(button_text, type="primary"):
                if user_choice:
                    selected_key = user_choice.split(":")[0]
                    
                    # Save user answer
                    if current_idx == len(st.session_state.user_answers):
                        st.session_state.user_answers.append(selected_key)
                    else:
                        st.session_state.user_answers[current_idx] = selected_key
                        
                    # Advance
                    if current_idx + 1 < total_qs:
                        st.session_state.current_index += 1
                    else:
                        st.session_state.quiz_finished = True
                        st.session_state.game_active = False
                    st.rerun()
                else:
                    st.toast("Please select an option first!", icon="⚠️")

# ==========================================
# SCREEN 3: GAME OVER
# ==========================================
elif st.session_state.quiz_finished:
    
    # Score Calculation for Simulation Mode
    if st.session_state.simulation_mode and "sim_scored" not in st.session_state:
        st.session_state.score = 0
        st.session_state.incorrect_indices = []
        for i, q in enumerate(st.session_state.quiz_data):
            # Check if answer was recorded
            user_ans = st.session_state.user_answers[i] if i < len(st.session_state.user_answers) else None
            if user_ans == q['answer_key']:
                st.session_state.score += 1
            else:
                st.session_state.incorrect_indices.append(q)
        st.session_state.sim_scored = True

    st.balloons()
    st.title("🎉 Session Complete!")
    
    final_score = st.session_state.score
    total = len(st.session_state.quiz_data)
    percent = (final_score / total) * 100
    
    # Save to History
    if "history_saved" not in st.session_state:
        st.session_state.history.append({
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Score": f"{final_score}/{total}",
            "Score (%)": round(percent, 1)
        })
        st.session_state.history_saved = True

    st.metric("Final Score", f"{final_score} / {total}", f"{percent:.1f}%")
    
    # --- NAVIGATION BUTTONS ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Home Screen"):
            if "history_saved" in st.session_state: del st.session_state.history_saved
            if "sim_scored" in st.session_state: del st.session_state.sim_scored
            st.session_state.quiz_finished = False
            st.session_state.game_active = False
            st.rerun()

    with col2:
        missed_qs = st.session_state.incorrect_indices
        if len(missed_qs) > 0:
            if st.button(f"🔁 Retry {len(missed_qs)} Missed"):
                if "history_saved" in st.session_state: del st.session_state.history_saved
                if "sim_scored" in st.session_state: del st.session_state.sim_scored
                
                st.session_state.quiz_data = missed_qs[:]
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.incorrect_indices = []
                st.session_state.user_answers = []
                st.session_state.quiz_finished = False
                st.session_state.game_active = True
                st.rerun()
        else:
            st.button("🔁 Retry Missed", disabled=True, help="You got everything right!")

    with col3:
        if st.button("🔄 New Exam"):
            if "history_saved" in st.session_state: del st.session_state.history_saved
            if "sim_scored" in st.session_state: del st.session_state.sim_scored
            
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.incorrect_indices = []
            st.session_state.user_answers = []
            st.session_state.quiz_finished = False
            st.session_state.game_active = False 
            st.rerun()
            
    st.write("---")

    # --- EXAM REVIEW (Always shows in Simulation Mode, or for reference in Study Mode) ---
    if st.session_state.simulation_mode:
        st.subheader("📝 Exam Review")
        st.write("Review your answers and the rationales below:")
        
        for i, q in enumerate(st.session_state.quiz_data):
            user_ans = st.session_state.user_answers[i] if i < len(st.session_state.user_answers) else "Skipped"
            correct_ans = q['answer_key']
            is_correct = user_ans == correct_ans
            
            # Create a collapsible box for each question
            icon = "✅" if is_correct else "❌"
            with st.expander(f"Question {i+1} {icon} (Click to expand)"):
                st.markdown(f"**{q['question_text']}**")
                
                # Show all options
                for key, val in sorted(q['options'].items()):
                    if key == correct_ans:
                        st.markdown(f"**{key}: {val}** *(Correct Answer)*")
                    elif key == user_ans:
                        st.markdown(f"*{key}: {val}* *(Your Answer)*")
                    else:
                        st.markdown(f"{key}: {val}")
                        
                st.info(f"**Rationale:** {q['rationale']}")


