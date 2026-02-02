import streamlit as st
import json

# 1. Load the Data
@st.cache_data
def load_questions():
    try:
        with open('exam_formatted_game.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: 'exam_formatted_game.json' not found.")
        return []

questions = load_questions()

# 2. Initialize Session State
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False
if 'answer_submitted' not in st.session_state:
    st.session_state.answer_submitted = False

# 3. Game Logic
if st.session_state.quiz_finished:
    # --- Game Over Screen ---
    st.balloons()
    st.title("🎉 Game Over!")
    
    total = len(questions)
    score = st.session_state.score
    percentage = (score / total) * 100
    
    st.metric(label="Final Score", value=f"{score} / {total}", delta=f"{percentage:.1f}%")
    
    if percentage >= 70:
        st.success("Great job! You passed.")
    else:
        st.warning("Keep studying!")
        
    if st.button("Restart Quiz"):
        st.session_state.current_index = 0
        st.session_state.score = 0
        st.session_state.quiz_finished = False
        st.session_state.answer_submitted = False
        st.rerun()

else:
    # --- Metrics Logic ---
    total_qs = len(questions)
    # Determine how many questions have been fully answered for the accuracy calculation
    qs_answered = st.session_state.current_index
    if st.session_state.answer_submitted:
        qs_answered += 1
        
    # Calculate current accuracy (avoid divide by zero)
    if qs_answered > 0:
        current_accuracy = st.session_state.score / qs_answered
    else:
        current_accuracy = 0.0

    # --- Display Progress & Accuracy Bars ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption(f"Question {st.session_state.current_index + 1} of {total_qs}")
        # Progress bar (0.0 to 1.0)
        progress_val = (st.session_state.current_index + 1) / total_qs
        st.progress(progress_val)
        
    with col2:
        st.caption(f"Current Accuracy: {current_accuracy:.0%}")
        # Accuracy bar (0.0 to 1.0)
        st.progress(current_accuracy)

    # --- Display Question ---
    q = questions[st.session_state.current_index]
    st.subheader(q['question_text'])
    
    # Display Options
    options = q['options']
    choice_labels = [f"{key}: {value}" for key, value in sorted(options.items())]
    
    # We use a key based on the index so the widget resets for new questions
    user_choice = st.radio("Choose your answer:", choice_labels, key=f"q_{st.session_state.current_index}", disabled=st.session_state.answer_submitted)
    
    # Submit Button
    if not st.session_state.answer_submitted:
        if st.button("Submit Answer"):
            st.session_state.answer_submitted = True
            st.rerun()
            
    else:
        # Check Answer
        selected_key = user_choice.split(":")[0] # Extract "A" from "A: text"
        correct_key = q['answer_key']
        
        if selected_key == correct_key:
            st.success("✅ Correct!")
            # We only increment score once per question
            if "scored_current" not in st.session_state: 
                st.session_state.score += 1
                st.session_state.scored_current = True
        else:
            st.error(f"❌ Incorrect. The correct answer was {correct_key}.")
            
        st.info(f"**Rationale:** {q['rationale']}")
        
        # Next Question Button
        if st.button("Next Question"):
            st.session_state.answer_submitted = False
            # Clean up the temporary flag
            if "scored_current" in st.session_state:
                del st.session_state.scored_current
                
            if st.session_state.current_index + 1 < len(questions):
                st.session_state.current_index += 1
            else:
                st.session_state.quiz_finished = True
            st.rerun()
