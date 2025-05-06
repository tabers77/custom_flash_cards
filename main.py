# -------
# TODO:
# -------
# git push
# improve the formatting of te questions ?
# add more questions


import os
import json
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from googleapiclient.discovery import build

# --- Load credentials ---
load_dotenv()
google_creds = json.loads(os.getenv("GOOGLE_CREDS"))
scope = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/spreadsheets'
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
docs_service = build('docs', 'v1', credentials=creds)
sheets_client = gspread.authorize(creds)

# --- Constants ---
# DOC_ID = "1DVtDAKzyPMwEJR9XJmb88OlfnNAyINyRH3kx12p4cQ4"
SHEET_ID = "1Yy3wg0ThnxnxwwAZBdAjcByoQeP2i9XKAn8dtaCQzTY"

# DOC_ID = "1JUSuVo6lvppfOWj_TxINWmNySDmjUEWOcurbvxPRLBs"  # NLP docs

DOC_ID = "1j17uqOoBx-8XUJ_Er2J4rsg4Q_HXqF0ZKyKqgaLb2w0"  # STATS


# --- Helper Functions ---
def extract_text_elements(doc):
    """Extract text elements from a Google Doc."""
    elements = doc.get("body", {}).get("content", [])
    texts = []
    for e in elements:
        para = e.get("paragraph")
        if para:
            line = ''.join(
                el.get("textRun", {}).get("content", "") for el in para.get("elements", [])
            ).strip()
            if line:
                texts.append(line)
    return texts


def parse_questions_and_answers(doc):
    """Parse questions and answers from a Google Doc."""
    qa_pairs = []
    question = None

    for element in doc['body']['content']:
        paragraph = element.get("paragraph")
        if not paragraph:
            continue

        line_text = ""
        is_question_line = False

        for el in paragraph.get("elements", []):
            text_run = el.get("textRun")
            if not text_run:
                continue

            text = text_run.get("content", "").strip()
            style = text_run.get("textStyle", {})
            font_size = style.get("fontSize", {}).get("magnitude")

            line_text += text + " "

            if text.startswith("Q.") and font_size == 15:
                is_question_line = True

        line_text = line_text.strip()

        if is_question_line:
            if question:
                qa_pairs.append(question)
            question = {
                "Question": line_text[2:].strip(),  # strip "Q."
                "Answer": ""
            }
        elif question and line_text:
            if question["Answer"]:
                question["Answer"] += " " + line_text
            else:
                question["Answer"] = line_text

    if question:
        qa_pairs.append(question)

    return qa_pairs


def filter_new_questions(qa_pairs, existing_questions):
    """Filter out duplicate questions."""
    return [pair for pair in qa_pairs if pair["Question"].strip() not in existing_questions]


def upload_to_google_sheet(sheet, rows):
    """Upload rows to a Google Sheet."""
    sheet.append_rows(rows)


# --- Main Logic ---
# Load Google Doc
doc = docs_service.documents().get(documentId=DOC_ID).execute()

# Parse questions and answers
qa_pairs = parse_questions_and_answers(doc)

# Load existing questions from the Google Sheet
# sheet1 = sheets_client.open_by_key(SHEET_ID).sheet1
# existing_records = sheet1.get_all_records()

sheet = sheets_client.open_by_key(SHEET_ID).worksheet("Sheet3")

existing_records = sheet.get_all_records()

existing_questions = set(record["Question"].strip() for record in existing_records)

# Filter new questions
new_qa_pairs = filter_new_questions(qa_pairs, existing_questions)

# Upload new questions to the Google Sheet
if new_qa_pairs:
    rows = [[pair["Question"], pair["Answer"], "", "Medium"] for pair in new_qa_pairs]
    upload_to_google_sheet(sheet, rows)
    print(f"✅ Added {len(rows)} new questions.")
else:
    print("🟡 No new questions to add.")
