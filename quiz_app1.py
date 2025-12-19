# Save this code as quiz_app.py
# ----------------------------------------------------------------------
# INSTRUCTIONS:
# 1. Open your terminal or command prompt and run:
#    pip install streamlit python-docx pyperclip
# 2. Run the application in the folder where you saved the file:
#    streamlit run quiz_app.py
# ----------------------------------------------------------------------

import streamlit as st
from docx import Document
import random
import time
import streamlit.components.v1 as components
import re
import io
import urllib.parse
import pyperclip

# --- CONSTANTS FOR EXTENDED OPTIONS ---
VALID_OPTIONS = ["A", "B", "C", "D", "E", "F"]
VALID_OPTION_CHARS_PATTERN = r'[a-fA-F]'

# --- 1. PARSING LOGIC & HELPERS ---

def is_valid_option_format(text):
    """Checks if a string starts with A-F followed by a separator and contains content."""
    if len(text) < 2 or text[0].upper() not in VALID_OPTIONS:
        return False
    
    # Check for standard separators: A: or A. or A)
    is_valid_separator = text[1] in [":", ".", ")"]
    # Check for parenthesis format: (A)
    is_valid_parenthesis = text.startswith("(") and len(text) >= 3 and text[2] == ')' and text[1].upper() in VALID_OPTIONS
    
    content_after_prefix = ""
    if is_valid_separator:
        # Check content after 'A.', 'B:', etc.
        content_after_prefix = re.sub(r'^[a-zA-Z][.:\)]\s*', '', text).strip()
    elif is_valid_parenthesis:
        # Check content after '(A)', '(B)', etc.
        content_after_prefix = re.sub(r'^\([a-zA-Z]\)\s*', '', text).strip()

    return bool(content_after_prefix)

def get_raw_option_text(option_text):
    """Strips any leading option prefix (A:, B., (C)) from the text."""
    # Pattern to match and remove prefixes: (optional parenthesis) Letter (:, ., or )) (optional parenthesis)
    return re.sub(r'^\s*[\(]?[a-zA-Z][\.:\)]?\s*', '', option_text).strip()

def add_option_prefixes(raw_option_texts):
    """Generates the A:, B:, C: prefixes automatically for a list of raw option texts."""
    prefixed_options = []
    for i, text in enumerate(raw_option_texts):
        if i < len(VALID_OPTIONS):
            prefix = VALID_OPTIONS[i]
            prefixed_options.append(f"{prefix}: {text}")
        else:
            prefixed_options.append(text)
    return prefixed_options


def parse_docx(uploaded_file):
    """Parses questions and options from a DOCX file, storing RAW option text."""
    doc = Document(uploaded_file)
    questions = []
    current_question_lines = []
    raw_options = [] # Store raw option text without generated prefix
    q_id = 1
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue
        
        text_lower = text.lower()
        
        # 1. Answer Line Detection: Finalize the current question
        if text_lower.startswith("correct answer") or text_lower.startswith("answer"):
            if current_question_lines and len(raw_options) >= 2:
                clean_line = text_lower.replace("correct answer", "").replace("answer", "").replace(":", "").strip()
                found_answers = re.findall(VALID_OPTION_CHARS_PATTERN, clean_line)
                correct_list = sorted(list(set([x.upper() for x in found_answers])))
                
                questions.append({
                    "id": q_id,
                    "question": "\n".join(current_question_lines).strip(),
                    "options": raw_options, # Store RAW options
                    "correct": correct_list
                })
                q_id += 1
            # Reset for the next question
            current_question_lines = []
            raw_options = []
            
        # 2. Option Detection: Starts an option sequence
        elif is_valid_option_format(text):
            # Extract raw text and store it
            raw_text = get_raw_option_text(text)
            raw_options.append(raw_text)
                
        # 3. Question Text: If we haven't started options, this must be question text.
        elif len(raw_options) == 0:
            current_question_lines.append(text)
                
    return questions

def parse_txt(uploaded_file):
    """Parses questions and options from a TXT file, storing RAW option text."""
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    questions = []
    current_question_lines = []
    raw_options = [] # Store raw option text without generated prefix
    q_id = 1
    
    for line in lines:
        text = line.strip()
        if not text: continue
        
        text_lower = line.strip().lower()
        
        # 1. Answer Line Detection: Finalize the current question
        if text_lower.startswith("correct answer") or text_lower.startswith("answer"):
            if current_question_lines and len(raw_options) >= 2:
                clean_line = text_lower.replace("correct answer", "").replace("answer", "").replace(":", "").strip()
                found_answers = re.findall(VALID_OPTION_CHARS_PATTERN, clean_line)
                correct_list = sorted(list(set([x.upper() for x in found_answers])))
                
                questions.append({
                    "id": q_id,
                    "question": "\n".join(current_question_lines).strip(),
                    "options": raw_options, # Store RAW options
                    "correct": correct_list
                })
                q_id += 1
            # Reset for the next question
            current_question_lines = []
            raw_options = []
            
        # 2. Option Detection: Starts an option sequence
        elif is_valid_option_format(text):
            # Extract raw text and store it
            raw_text = get_raw_option_text(text)
            raw_options.append(raw_text)
                
        # 3. Question Text: If we haven't started options, this must be question text.
        elif len(raw_options) == 0:
            current_question_lines.append(text)
                
    return questions

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Exam Simulator", layout="wide")

# --- 3. CUSTOM CSS (Cyan/Light Green Theme) ---
st.markdown("""
<style>
    /* 1. CYAN BACKGROUND */
    .stApp { background-color: #e0f7fa; color: #1f2937; } /* Light cyan background */
    
    /* 2. GENERAL TEXT COLOR */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { color: #1f2937; } /* Dark text for contrast */

    /* HIDE HEADER */
    header {visibility: hidden;}
    .block-container { padding-top: 1rem !important; padding-bottom: 5rem; }
    
    /* LIGHT GREEN PRIMARY BUTTONS (Replaces Orange) */
    div.stButton > button[kind="primary"] {
        background-color: #4CAF50 !important; /* Original Light Green */
        border-color: #4CAF50 !important;
        color: white !important;
        font-weight: bold; /* BOLD TEXT */
        font-size: 16px !important;
        padding: 8px 20px !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #45a049 !important; /* Slightly darker hover */
        border-color: #45a049 !important;
    }
    
    /* SECONDARY BUTTONS (Replaces Orange) */
    div.stButton > button[kind="secondary"] {
        border: 2px solid #4CAF50;
        color: #4CAF50;
        font-weight: bold; /* BOLD TEXT */
        background-color: #ffffff; /* White background */
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #f7fff7; /* Very light green hover */
    }
    
    /* --- STUDY MODE: Answer Card --- */
    .answer-card {
        padding: 15px; border-left: 5px solid #15803d;
        background-color: #f0fdf4; /* Light green background */
        color: #15803d;
        border-radius: 5px; margin-top: 10px;
    }
    .answer-card h5 { color: #15803d; margin: 0; }

    /* Ensure options look normal (not greyed out) */
    div[data-testid="stRadio"] label,
    div[data-testid="stCheckbox"] label,
    div[data-testid="stRadio"] div[data-baseweb="radio"] div:nth-child(2) p,
    div[data-testid="stCheckbox"] div[data-baseweb="checkbox"] div:nth-child(2) p {
        opacity: 1 !important;
        color: #1f2937 !important; /* Dark text for contrast */
    }
    
    /* Status Bar Pills */
    .stat-pill {
        padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 13px; display: flex; align-items: center; white-space: nowrap;
    }
    .stat-blue { background-color: #eff6ff; color: #1d4ed8; border: 1px solid #dbeafe; }
    .stat-green { background-color: #f0fdf4; color: #15803d; border: 1px solid #dcfce7; }
    .stat-red { background-color: #fef2f2; color: #b91c1c; border: 1px solid #fee2e2; }
    /* Yellow/Follow Up color */
    .stat-yellow { background-color: #fff8e1; color: #d97706; border: 1px solid #fef3c7; }

    /* CARDS */
    .question-card {
        background-color: #ffffff; /* White Card Background */
        padding: 15px 20px; border-radius: 10px;
        border: 1px solid #d1d5db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    /* FIX: Ensure question text starts clean */
    .question-text {
        font-size: 20px !important; font-weight: 700; color: #1f2937; /* Dark text */
        margin: 0;
        white-space: pre-wrap;
    }
    
    div.stButton > button { border-radius: 6px; }
    
    /* Subtle 'All The Best' */
    .subtle-all-the-best {
        text-align: center; font-size: 24px; font-weight: 600; color: #4b5563; /* Medium grey */
        opacity: 0.8; animation: fadeIn 2s ease-in;
    }
    @keyframes fadeIn { 0% {opacity: 0;} 100% {opacity: 1;} }

    /* Custom CSS to hide the radio/checkbox prefix (A:, B:, etc.) in Exam Mode */
    /* This rule applies to all modes, but the displayed options are cleaned only in Exam Mode */
    div[data-baseweb="radio"] > div:first-child p,
    div[data-baseweb="checkbox"] > div:first-child p {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. STATE INITIALIZATION ---
if 'quiz_data' not in st.session_state: st.session_state.quiz_data = []
if 'current_index' not in st.session_state: st.session_state.current_index = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'quiz_finished' not in st.session_state: st.session_state.quiz_finished = False
if 'start_time' not in st.session_state: st.session_state.start_time = time.time()
if 'quiz_start_time' not in st.session_state: st.session_state.quiz_start_time = time.time()
if 'exam_name' not in st.session_state: st.session_state.exam_name = ""
if 'quiz_mode' not in st.session_state: st.session_state.quiz_mode = None
if 'follow_up_questions' not in st.session_state: st.session_state.follow_up_questions = []
if 'show_answer_study' not in st.session_state: st.session_state.show_answer_study = False
if 'shuffled_options_map' not in st.session_state: st.session_state.shuffled_options_map = {}

# --- 5. HELPER FUNCTIONS ---

def get_shuffled_options(q_id, raw_options, is_exam_mode):
    """
    Shuffles options for the given question ID once and stores the mapping.
    Returns: List of tuples (raw_text, original_prefix_char)
    """
    if is_exam_mode:
        # Exam Mode: Use the original order (A, B, C...)
        option_tuples = []
        for i, raw_text in enumerate(raw_options):
            if i < len(VALID_OPTIONS):
                option_tuples.append((raw_text, VALID_OPTIONS[i]))
        return option_tuples
    
    # Study Mode: Shuffle and cache the shuffled order (raw text)
    if q_id not in st.session_state.shuffled_options_map:
        # Create list of (raw_text, original_prefix_char) tuples based on original order
        option_tuples = []
        for i, raw_text in enumerate(raw_options):
            if i < len(VALID_OPTIONS):
                option_tuples.append((raw_text, VALID_OPTIONS[i]))
            
        random.shuffle(option_tuples)
        st.session_state.shuffled_options_map[q_id] = option_tuples
    
    return st.session_state.shuffled_options_map[q_id]

def toggle_show_answer():
    st.session_state.show_answer_study = not st.session_state.show_answer_study

def toggle_follow_up():
    """Toggles follow-up status. Does NOT move to the next question."""
    idx = st.session_state.current_index
    q_data = st.session_state.quiz_data[idx]
    q_id = q_data["id"]
    
    if q_id in st.session_state.follow_up_questions:
        st.session_state.follow_up_questions.remove(q_id)
    else:
        st.session_state.follow_up_questions.append(q_id)

def go_to_main_screen():
    """Resets states to return to the Setup Screen (clearing quiz_data forces re-upload)."""
    st.session_state.quiz_data = []
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_finished = False
    st.session_state.start_time = time.time()
    st.session_state.quiz_start_time = time.time()
    st.session_state.exam_name = ""
    st.session_state.quiz_mode = None
    st.session_state.follow_up_questions = []
    st.session_state.show_answer_study = False
    st.session_state.shuffled_options_map = {}

def go_next_study():
    st.session_state.current_index += 1
    st.session_state.start_time = time.time()
    st.session_state.show_answer_study = False

def go_prev_study():
    st.session_state.current_index -= 1
    st.session_state.start_time = time.time()
    st.session_state.show_answer_study = False

def explore_question(q_data):
    """Copies the entire question and options to clipboard and opens ChatGPT URL."""
    question_text = q_data["question"]
    # Pass the original raw options for the external tool
    options_text = "\n".join(q_data["options"])
    
    full_query = f"Explain this quiz question and identify the correct answer:\n\nQuestion: {question_text}\n\nOptions:\n{options_text}"
    
    try:
        pyperclip.copy(full_query)
        st.success("Question and options copied to your clipboard! Paste it into the new tab.")
    except Exception as e:
        st.error(f"Could not automatically copy the text. Please manually copy the following text and paste it into the new tab:")
        st.code(full_query, language="text")
        
    chat_url = "https://chatgpt.com/"
    
    components.html(
        f"""
        <script>
            window.open("{chat_url}", "_blank");
        </script>
        """,
        height=0,
        width=0
    )
    pass

def reset_exam_progress():
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_finished = False
    st.session_state.start_time = time.time()
    st.session_state.quiz_start_time = time.time()
    st.session_state.follow_up_questions = []
    st.session_state.shuffled_options_map = {}
    
def start_review_mode(question_ids_to_review):
    """Filters quiz_data to only include specified question IDs and switches to Study Mode."""
    if not question_ids_to_review:
        st.warning("No questions to review.")
        return

    # Map current question ID (from original list) to the question object
    id_to_question_map = {q['id']: q for q in st.session_state.quiz_data}
    
    # Filter and re-order questions
    reviewed_questions = [id_to_question_map[q_id] for q_id in question_ids_to_review if q_id in id_to_question_map]

    # Overwrite session state with the filtered set
    st.session_state.quiz_data = reviewed_questions
    st.session_state.exam_name = f"Review: {st.session_state.exam_name}"
    st.session_state.quiz_mode = "Study Mode"
    st.session_state.current_index = 0
    st.session_state.quiz_finished = False
    st.session_state.user_answers = {}
    st.session_state.show_answer_study = True
    st.session_state.shuffled_options_map = {}


# ==========================================
# SCREEN 3: RESULTS (Exam Mode Only) - Highest Priority Check
# ==========================================
if st.session_state.quiz_finished and st.session_state.quiz_data:
    st.balloons()
    final = st.session_state.score
    total = len(st.session_state.quiz_data)
    
    # Calculate Percentage Score
    percentage = (final / total) * 100 if total > 0 else 0
    
    # Calculate Total Time Taken
    end_time = time.time()
    start_time_for_duration = st.session_state.get('quiz_start_time', end_time)
    total_duration = int(end_time - start_time_for_duration)
    
    # Format HH:MM:SS
    mm, ss = divmod(total_duration, 60)
    hh, mm = divmod(mm, 60)
    time_taken_str = f"{hh:02}:{mm:02}:{ss:02}"

    # --- Score Output ---
    st.markdown(f"### 🏆 {st.session_state.exam_name} Ended")
    
    # Adjusted card for new theme
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 10px; background-color: white; border: 2px solid #4CAF50; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #4CAF50; margin-bottom: 10px;">Your Score is **{percentage:.1f}%**</h2>
        <p style="font-size: 18px; font-weight: 600; color: #4b5563;">
            Time taken: ⏱️ **{time_taken_str}** | Correct: **{final}** | Total: **{total}**
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # --- Detailed Review Section ---
    
    # 1. Identify Incorrectly Answered Questions IDs
    incorrect_q_ids = set()
    for index, q_data in enumerate(st.session_state.quiz_data):
        q_id = q_data['id']
        # The user_answers store the actual prefixed option string (e.g., 'A: Option text')
        user_choice = st.session_state.user_answers.get(index)
        
        if user_choice not in (None, "Time Out", 'STUDY_REVIEW_NO_SELECTION'):
            is_correct = False
            correct_answers_list = q_data['correct']
            
            # Extract the option character(s) from the user's saved choice(s)
            if isinstance(user_choice, list): # Multiple choice
                # Get the first character of the prefixed string (A: Option)
                user_chars = sorted([x.strip()[0].upper() for x in user_choice])
            elif user_choice and isinstance(user_choice, str): # Single choice
                user_chars = [user_choice.strip()[0].upper()]
            else:
                user_chars = []
                
            if user_chars == correct_answers_list:
                is_correct = True
            
            if not is_correct:
                incorrect_q_ids.add(q_id)

    # 2. Extract Manually Followed-up Questions IDs
    manual_follow_up_ids = set(st.session_state.follow_up_questions)
    
    st.markdown("### 📝 Detailed Review")
    
    # Wrongly Answered Questions Display
    if incorrect_q_ids:
        wrong_list_str = ", ".join(map(str, sorted(list(incorrect_q_ids))))
        st.markdown(f"""
        <div style="padding: 10px; border-left: 5px solid #b91c1c; background-color: #fef2f2; margin-bottom: 15px; color: #b91c1c;">
            <h5 style="color: #b91c1c; margin: 0;">❌ Wrongly Answered Questions (IDs):</h5>
            <p style="margin: 5px 0 0 0; font-weight: bold;">{wrong_list_str}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success("You answered all questions correctly!")
        
    # Manually Followed-up Questions Display (Used stat-yellow color)
    if manual_follow_up_ids:
        follow_up_list_str = ", ".join(map(str, sorted(list(manual_follow_up_ids))))
        st.markdown(f"""
        <div style="padding: 10px; border-left: 5px solid #d97706; background-color: #fffbeb; margin-bottom: 15px; color: #b45309;">
            <h5 style="color: #d97706; margin: 0;">❓ Manually Followed-up Questions (IDs):</h5>
            <p style="margin: 5px 0 0 0; font-weight: bold;">{follow_up_list_str}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("---")

    # --- Options for Next Step (Including Review Button) ---
    
    review_ids = sorted(list(incorrect_q_ids.union(manual_follow_up_ids)))
    
    col_review, col_restart, col_new = st.columns([2, 2, 2])

    with col_review:
        if review_ids:
            if st.button(f"🎯 Review {len(review_ids)} Focus Questions", key="start_review_btn", type="primary", help="Start a Study Mode session with only the questions you got wrong or flagged."):
                start_review_mode(review_ids)
                st.rerun()
        
    with col_restart:
        if st.button("🔄 Restart Exam", type="secondary", on_click=reset_exam_progress):
            st.rerun()

    with col_new:
        if st.button("🏠 Go to Main Screen", type="secondary", on_click=go_to_main_screen):
            st.rerun()

# ==========================================
# SCREEN 1 & 2: SETUP OR INTERFACE
# ==========================================
elif st.session_state.quiz_data:
    
    # --- IF QUIZ DATA EXISTS, GO TO INTERFACE (SCREEN 2) ---
    
    idx = st.session_state.current_index
    total_q = len(st.session_state.quiz_data)
    q_data = st.session_state.quiz_data[idx]
    
    # Get the raw option text list (from parser)
    raw_option_texts = q_data['options']
    
    is_exam_mode = st.session_state.quiz_mode == "Exam Mode"
    
    # Get options list: [(raw_text, original_prefix_char), ...] (shuffled in Study, original order in Exam)
    current_shuffled_tuples = get_shuffled_options(q_data['id'], raw_option_texts, is_exam_mode)
    
    # Create the final list for display and a mapping for prefix generation
    prefixed_options_map = {} # {display_text: {prefixed_string, original_char, is_correct}}
    
    for i, (raw_text, original_char) in enumerate(current_shuffled_tuples):
        # Generate the prefix based on the SHUFFLED/CURRENT display order (A, B, C...)
        prefix = VALID_OPTIONS[i]
        
        # Determine the correct state for highlighting
        is_correct = original_char in q_data['correct']
        
        # Store the display string (raw text) and the full prefixed string (for saving/scoring)
        prefixed_string = f"{prefix}: {raw_text}"
        
        if is_exam_mode:
            # Exam Mode: Display without prefixes
            display_string = raw_text
        else:
            # Study Mode: Display with A:, B:, C: prefixes
            display_string = prefixed_string

        # Use the raw text (Exam Mode) or prefixed text (Study Mode) as the key for reliable mapping
        prefixed_options_map[display_string] = {
            'prefixed_string': prefixed_string,
            'original_char': original_char,
            'is_correct': is_correct
        }

    current_options_for_display = list(prefixed_options_map.keys())
    
    # --- COMMON HEADER ---
    col_title, col_controls = st.columns([3, 1.2])
    with col_title:
        st.markdown(f"### 📝 {st.session_state.exam_name} ({st.session_state.quiz_mode})")
        
    with col_controls:
        # Calculate Total Elapsed Time
        total_elapsed = int(time.time() - st.session_state.quiz_start_time)
        
        timer_id = "total_timer_display" if is_exam_mode else "study_timer_display"
        
        # Adjusted Timer background/text colors for light theme
        timer_html = f"""
        <div style="text-align: right; margin-bottom: 10px;">
            <div id="{timer_id}" style="font-size: 18px; font-weight: bold; color: #4b5563; background: #e5e7eb; padding: 5px 15px; border-radius: 20px; display: inline-block;">
                ⏱️ 00:00:00
            </div>
        </div>
        <script>
            var startTimestamp = Date.now() - ({total_elapsed} * 1000);
            setInterval(function() {{
                var now = Date.now();
                var diff = Math.floor((now - startTimestamp) / 1000);
                var h = Math.floor(diff / 3600);
                var m = Math.floor((diff % 3600) / 60);
                var s = diff % 60;
                if (h < 10) h = "0" + h;
                if (m < 10) m = "0" + m;
                if (s < 10) s = "0" + s;
                document.getElementById("{timer_id}").innerHTML = "⏱️ " + h + ":" + m + ":" + s;
            }}, 1000);
        </script>
        """
        components.html(timer_html, height=45)
    
    # -------------------------------------------------------------------------
    # A. EXAM MODE LOGIC
    # -------------------------------------------------------------------------
    if is_exam_mode:
        
        # Stats & Controls
        attended = len(st.session_state.user_answers)
        correct = st.session_state.score
        wrong = attended - correct
        
        # Display stat cards
        c1, c2, c3, c4, c_end, c_reset, c_spacer = st.columns([1.2, 1.2, 1.2, 1.5, 1, 1, 2.9])
        with c1: st.markdown(f'<div class="stat-pill stat-blue">📝 Attended: {attended}/{total_q}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-pill stat-green">✅ Correct: {correct}</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-pill stat-red">❌ Wrong: {wrong}</div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-pill stat-yellow">❓ Follow Up: {len(st.session_state.follow_up_questions)}</div>', unsafe_allow_html=True)
        
        with c_end:
            if st.button("⏹ End", key="end_btn"): st.session_state.quiz_finished = True; st.rerun()
        with c_reset:
            if st.button("🔄 Reset", key="rst_btn", on_click=reset_exam_progress):
                st.rerun()

        st.write("---")

        previous_choice_prefixed = st.session_state.user_answers.get(idx, None)
        is_answered = previous_choice_prefixed is not None and previous_choice_prefixed != 'STUDY_REVIEW_NO_SELECTION'
        
        # Timer (180s limit for the question)
        time_limit = 180
        elapsed = time.time() - st.session_state.start_time
        remaining_seconds = max(0, int(time_limit - elapsed))
        
        # Format HH:MM:SS
        mm, ss = divmod(remaining_seconds, 60)
        hh, mm = divmod(mm, 60)
        initial_str = f"{hh:02}:{mm:02}:{ss:02}"
        
        col_q_timer, col_q_space = st.columns([1, 6])
        if not is_answered:
            timer_html = f"""
                <style>@keyframes blinker {{ 50% {{ opacity: 0; }} }} .blink_me {{ animation: blinker 0.5s linear infinite; color: red !important; }}</style>
                <div id="countdown" style="font-weight: bold; font-size: 18px; color: #10b981;">⏳ {initial_str}</div>
                <script>
                    var timeleft = {remaining_seconds};
                    var element = document.getElementById("countdown");
                    var downloadTimer = setInterval(function(){{
                    if(timeleft <= 0){{ clearInterval(downloadTimer); element.innerHTML = "🔴 Time Up!"; element.style.color = "red"; }}
                    else {{
                        var h = Math.floor(timeleft / 3600);
                        var m = Math.floor((timeleft % 3600) / 60);
                        var s = timeleft % 60;
                        if (h < 10) h = "0" + h;
                        if (m < 10) m = "0" + m;
                        if (s < 10) s = "0" + s;
                        
                        element.innerHTML = "⏳ " + h + ":" + m + ":" + s + " Left";
                        
                        if (timeleft > 60) element.style.color = "#10b981";
                        else if (timeleft > 30) element.style.color = "#f59e0b";
                        else {{ element.style.color = "#ef4444"; }}
                        
                        if (timeleft <= 20) element.classList.add("blink_me");
                    }}
                    timeleft -= 1;
                    }}, 1000);
                </script>
            """
            with col_q_timer: components.html(timer_html, height=50)
        else:
            col_q_timer.markdown("⏹ **Stopped**")

        # Question Card (No Question X of Y in Exam Mode)
        st.markdown(f'<div class="question-card"><div class="question-text">{q_data["question"]}</div></div>', unsafe_allow_html=True)

        # Options
        correct_answers_list = q_data['correct']
        is_multiple_choice = len(correct_answers_list) > 1
        user_selection_to_save = None
        
        # Get the displayed option text corresponding to the saved prefixed answer (for radio pre-selection)
        previous_choice_display = get_raw_option_text(previous_choice_prefixed) if previous_choice_prefixed and isinstance(previous_choice_prefixed, str) else None

        if is_multiple_choice:
            st.caption("ℹ️ **Select all that apply**")
            checkbox_answers_prefixed = []
            if is_answered:
                # Review Mode for Checkbox
                user_picked_opts_prefixed = previous_choice_prefixed if isinstance(previous_choice_prefixed, list) else []
                for opt_display in current_options_for_display:
                    opt_map = prefixed_options_map[opt_display]
                    
                    is_correct_opt = opt_map['is_correct']
                    is_picked = opt_map['prefixed_string'] in user_picked_opts_prefixed
                    
                    label = opt_display
                    if is_correct_opt: label = f":green[**✅ {opt_display} (Correct)**]"
                    elif is_picked and not is_correct_opt: label = f":red[**❌ {opt_display} (Wrong)**]"
                    st.checkbox(label, value=is_picked, disabled=True, key=f"chk_{q_data['id']}_{opt_map['original_char']}")
            else:
                # Active Checkbox
                for i, opt_display in enumerate(current_options_for_display):
                    # In active mode, we store the full prefixed string for correct scoring
                    opt_prefixed = prefixed_options_map[opt_display]['prefixed_string']
                    if st.checkbox(opt_display, key=f"active_chk_{q_data['id']}_{i}"): checkbox_answers_prefixed.append(opt_prefixed)
                user_selection_to_save = checkbox_answers_prefixed
        else:
            display_options = []
            selected_option_index = None
            if is_answered:
                # Review Mode for Radio
                for i, opt_display in enumerate(current_options_for_display):
                    opt_map = prefixed_options_map[opt_display]
                    
                    if opt_map['is_correct']: 
                        display_options.append(f":green[**✅ {opt_display} (Correct)**]")
                    elif opt_display == previous_choice_display and not opt_map['is_correct']: 
                        display_options.append(f":red[**❌ {opt_display} (Your Answer)**]")
                    else: 
                        display_options.append(opt_display)
                    
                    if opt_display == previous_choice_display: selected_option_index = i
                
            else:
                # Active Radio
                display_options = current_options_for_display
                selected_option_index = None

            # Radio buttons: We capture the selected raw text, then map it to the prefixed version for saving
            user_selection_display = st.radio("Options:", display_options, index=selected_option_index, key=f"radio_{q_data['id']}", disabled=is_answered, label_visibility="collapsed")
            
            if not is_answered and user_selection_display is not None:
                # Map the user's displayed selection (raw text) back to the prefixed version for saving
                user_selection_prefixed = prefixed_options_map[user_selection_display]['prefixed_string']
                user_selection_to_save = user_selection_prefixed
            elif is_answered:
                # In review mode, use the previously saved full string
                user_selection_to_save = previous_choice_prefixed


        st.write("")
        c_sub, c_next, c_f = st.columns([1, 1, 4])
        
        # SUBMIT button logic
        with c_sub:
            if st.button("Submit", type="primary", disabled=is_answered):
                
                # Check for Time Out submission
                if remaining_seconds <= 0:
                    st.session_state.user_answers[idx] = "Time Out"
                    st.rerun()
                    
                has_input = (len(user_selection_to_save) > 0) if is_multiple_choice and isinstance(user_selection_to_save, list) else (user_selection_to_save is not None)
                if has_input:
                    
                    st.session_state.user_answers[idx] = user_selection_to_save
                    
                    # Score calculation (based on saved prefixed string)
                    is_correct_submission = False
                    if is_multiple_choice:
                        user_chars = sorted([x.strip()[0].upper() for x in user_selection_to_save])
                        if user_chars == correct_answers_list:
                            is_correct_submission = True
                    else:
                        if user_selection_to_save and user_selection_to_save.strip()[0].upper() == correct_answers_list[0]:
                            is_correct_submission = True
                        
                    # Instant Feedback
                    if is_correct_submission:
                            st.session_state.score += 1
                            st.toast("✅ Correct Answer! Great job.", icon='🎉')
                    else:
                            st.toast("❌ Incorrect. Review the options.", icon='🚨')
                            
                    st.rerun()
                else: st.warning("Select option(s)")

        # NEXT button logic
        with c_next:
            can_proceed = is_answered or (remaining_seconds <= 0) or (q_data["id"] in st.session_state.follow_up_questions)
            if idx + 1 < total_q:
                if st.button("Next Question ➡", disabled=not can_proceed):
                    st.session_state.current_index += 1; st.session_state.start_time = time.time(); st.rerun()
            else:
                if st.button("Finish Quiz", type="primary", disabled=not can_proceed):
                    st.session_state.quiz_finished = True; st.rerun()
        
        # FOLLOW UP button (placed below submit/next)
        st.write("")
        is_followed_up = q_data["id"] in st.session_state.follow_up_questions
        follow_btn_text = "⭐ Unmark Follow Up" if is_followed_up else "❓ Follow Up Later"
        
        if st.button(follow_btn_text, key="follow_up_btn_below", type="secondary", on_click=toggle_follow_up):
            st.rerun()

    # -------------------------------------------------------------------------
    # B. STUDY MODE LOGIC
    # -------------------------------------------------------------------------
    elif st.session_state.quiz_mode == "Study Mode":
        
        # Question Card with Progress (Study mode keeps Question X of Y)
        q_id_display = idx + 1
        st.markdown(f'<div class="question-card"><p style="font-size: 14px; color: #4b5563; font-weight: 600; margin-bottom: 5px;">Question {q_id_display} of {total_q}</p><div class="question-text">{q_data["question"]}</div></div>', unsafe_allow_html=True)
        
        correct_answers_list = q_data['correct']
        is_multi = len(correct_answers_list) > 1
        
        is_review_mode = st.session_state.show_answer_study
        
        st.caption("ℹ️ Selection in Study Mode is for practice only and has no effect on score.")

        
        # --- OPTIONS DISPLAY ---

        if is_multi:
            st.caption("ℹ️ **Select all that apply**")
            
            if is_review_mode:
                for opt_prefixed in current_options_for_display:
                    opt_map = prefixed_options_map[opt_prefixed]
                    is_correct_opt = opt_map['is_correct']
                    label = opt_prefixed
                    
                    if is_correct_opt:
                        label = f":green[**✅ {opt_prefixed} --> Is the correct answer**]"
                    
                    # DISABLED=FALSE ensures options are not greyed out
                    st.checkbox(label, value=False, disabled=False, key=f"study_chk_review_{q_data['id']}_{opt_map['original_char']}")
            else:
                # Active Checkbox
                for i, opt_prefixed in enumerate(current_options_for_display):
                    st.checkbox(opt_prefixed, key=f"study_chk_active_{q_data['id']}_{i}")
        else:
            display_options = []
            selected_index = None
            
            if is_review_mode:
                for i, opt_prefixed in enumerate(current_options_for_display):
                    opt_map = prefixed_options_map[opt_prefixed]
                    
                    if opt_map['is_correct']:
                        display_options.append(f":green[**✅ {opt_prefixed} --> Is the correct answer**]")
                    else:
                        display_options.append(opt_prefixed)
                    
            else:
                display_options = current_options_for_display
                
            # DISABLED=FALSE ensures options are not greyed out
            st.radio("Options:", display_options, index=selected_index, key=f"study_radio_{q_data['id']}", disabled=False, label_visibility="collapsed")


        # --- Show Answer / Explore Buttons ---
        st.write("---")
        
        # BUTTON LAYOUT: Previous | Show Answer | Next | Explore | Go to Main Screen
        c_prev, c_ans, c_next, c_explore, c_exit = st.columns([1, 1, 1, 1.8, 1])
        
        with c_prev:
            if idx > 0:
                if st.button("⬅ Previous", on_click=go_prev_study): st.rerun()
        
        with c_ans:
            if is_review_mode:
                if st.button("↩️ Hide Answer", on_click=toggle_show_answer, key="hide_btn", type="secondary"): st.rerun()
            else:
                if st.button("💡 Show Answer", on_click=toggle_show_answer, key="show_btn", type="primary"): st.rerun()

        with c_next:
            if idx + 1 < total_q:
                if st.button("Next ➡", type="primary", on_click=go_next_study): st.rerun()
            else:
                st.success("End of Questions")

        with c_explore:
            if st.button("🌍 Explore more about this question", key="explore_btn", type="secondary"):
                explore_question(q_data)
        
        with c_exit:
            if st.button("🏠 Exit Study", key="exit_study_btn", type="secondary", on_click=go_to_main_screen): st.rerun()


# ==========================================
# SCREEN 1: SETUP/UPLOAD (Lowest Priority Check - Only runs if quiz_data is empty)
# ==========================================
else:
    st.title("📚 Streamlit Quiz & Exam Simulator")
    st.markdown("Easily load and practice questions from DOCX or TXT files.")
    
    st.write("---")

    col_upload, col_mode = st.columns([2, 1])

    with col_upload:
        st.subheader("1. Upload Questions File")
        uploaded_file = st.file_uploader(
            "Upload a **.docx** or **.txt** file containing your questions. "
            "Questions should be separated by an 'Answer:' line.",
            type=["docx", "txt"]
        )
        exam_name = st.text_input("Enter Exam/Quiz Name (Optional)", key="exam_name_input")

    with col_mode:
        st.subheader("2. Select Mode")
        quiz_mode = st.radio(
            "Choose a practice mode:",
            options=["Exam Mode", "Study Mode"],
            index=0,
            key="quiz_mode_radio"
        )
        st.info(f"**{quiz_mode}** selected.")
        
    st.write("---")

    if st.button("🚀 Start Quiz", type="primary", disabled=uploaded_file is None):
        if uploaded_file is not None:
            # 1. Parsing the file
            with st.spinner("Processing questions..."):
                file_extension = uploaded_file.name.split('.')[-1].lower()
                if file_extension == 'docx':
                    questions = parse_docx(uploaded_file)
                elif file_extension == 'txt':
                    questions = parse_txt(uploaded_file)
                else:
                    st.error("Unsupported file type.")
                    st.stop()
            
            # 2. Saving to session state
            if questions:
                
                # SHUFFLE ONLY FOR EXAM MODE (Question order shuffle)
                if quiz_mode == "Exam Mode":
                    random.shuffle(questions)
                    st.info("Questions have been shuffled for a realistic Exam Mode experience.")
                else: # Study Mode: Sequential order
                    st.info("Questions are in the original sequential order for Study Mode.")
                
                st.session_state.quiz_data = questions
                st.session_state.exam_name = exam_name if exam_name else uploaded_file.name.rsplit('.', 1)[0]
                st.session_state.quiz_mode = quiz_mode
                st.session_state.quiz_start_time = time.time() # Start the main timer
                st.session_state.start_time = time.time() # Start the first question timer
                st.session_state.current_index = 0 # Ensure we start at the first question
                st.session_state.user_answers = {} # Clear any prior answers
                st.session_state.shuffled_options_map = {} # Clear shuffle map for a fresh start
                st.success(f"Successfully loaded **{len(questions)}** questions!")
                st.rerun()
            else:
                st.warning("Could not find any questions in the file. Please check the format.")
                
    st.markdown("""
        <div class="subtle-all-the-best">All The Best!</div>
        """, unsafe_allow_html=True)