import os
import json
import random
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ------------------ CONFIG ------------------

load_dotenv()
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
google_creds = json.loads(os.getenv("GOOGLE_CREDS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

# Open your spreadsheet
sheet = client.open("test").sheet1
data = sheet.get_all_records()

# Convert to DataFrame
df = pd.DataFrame(data)

# Ensure 'Difficulty' column exists
if 'Difficulty' not in df.columns:
    df['Difficulty'] = 'Medium'

# ------------------ APP STATE ------------------

if 'shown_indices' not in st.session_state:
    st.session_state.shown_indices = set()
if 'current_index' not in st.session_state:
    st.session_state.current_index = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False


# ------------------ PICK NEXT QUESTION ------------------

def pick_next_question():
    remaining = df[~df.index.isin(st.session_state.shown_indices)]
    if remaining.empty:
        st.session_state.shown_indices = set()
        remaining = df

    # Weighted selection: Hard = 3, Medium = 2, Easy = 1
    weights = remaining['Difficulty'].map({'Hard': 3, 'Medium': 2, 'Easy': 1}).fillna(1)
    st.session_state.current_index = random.choices(remaining.index.tolist(), weights=weights.tolist(), k=1)[0]
    st.session_state.show_answer = False  # reset answer visibility


# ------------------ UI ------------------

st.title("🧠 ML/DS Flashcards")

# If no question picked yet, pick one
if st.session_state.current_index is None:
    pick_next_question()

q_row = df.loc[st.session_state.current_index]
st.markdown(f"### ❓ {q_row['Question']}")

if st.button("💡 Show Answer"):
    st.session_state.show_answer = True
    st.rerun()

if st.session_state.show_answer:
    if q_row['Answer']:
        st.markdown(f"**Answer:** {q_row['Answer']}")
    elif q_row.get('Link'):
        st.markdown(f"[View answer here]({q_row['Link']})")
    else:
        st.markdown("_No answer provided._")

difficulty = st.radio("How difficult was this?", ["Easy", "Medium", "Hard"], horizontal=True)

if st.button("➡️ Next Question"):
    current_index = st.session_state.current_index
    df.at[current_index, 'Difficulty'] = difficulty
    st.session_state.shown_indices.add(current_index)

    # Save difficulty to Google Sheet
    sheet_row = current_index + 2  # +2 because sheet rows start at 1 and row 1 is header
    difficulty_col = df.columns.get_loc("Difficulty") + 1  # +1 because sheets are 1-indexed
    sheet.update_cell(sheet_row, difficulty_col, difficulty)

    pick_next_question()
    st.rerun()

# streamlit run app.py
