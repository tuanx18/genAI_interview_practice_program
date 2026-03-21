# Interview Trainer AI Chatbot

**A powerful desktop tool to practice technical interview questions with real-time AI grading and feedback.**

Built for Spark, Data Engineering, System Design, and other technical roles.  
You answer → GPT-4o-mini scores you (0–10) + gives detailed feedback + improvement tips + bonus suggestions.

---

## ✨ Features

- Random question engine (no repeats in one session)
- Category filter – practice only the topics you want
- Live timer per question + Reset Timer button
- "Read more" button – opens external link or lets you add one instantly
- Smart AI feedback with:
  - Colored score (green/orange/red)
  - Bold sections: **What You Did Well**, **How to Improve**, **Bonus Points Suggestions**
  - Scrollable content + separate Reference/Model Answer section
- Retry / Replace last attempt on the same question
- History viewer:
  - All history
  - Only current question history
  - Sort by score, time, or ID
- Debug mode (prints full prompt + GPT response to console)
- Professional Question Builder (`builder.py`) – easy GUI to add/edit questions
- Loading spinner while waiting for AI
- Copy Feedback button
- History saved permanently in `history.jsonl`

---

## Screenshots

### 1. Sample question display

<img width="1920" height="1027" alt="image" src="https://github.com/user-attachments/assets/e8267307-4b68-4d49-96fb-29cb01f447f7" />

### 2. Display AI-generated result after a submission

<img width="1916" height="1030" alt="image" src="https://github.com/user-attachments/assets/d03e6cd5-67ef-48eb-a778-696da698c355" />

### 3. Show record history

<img width="939" height="683" alt="image" src="https://github.com/user-attachments/assets/a2d76afc-f3d9-4bbc-a58c-7b06747405ba" />

### 4. Builder tool (for expanding the bank)

<img width="1920" height="1029" alt="image" src="https://github.com/user-attachments/assets/b7125774-77b8-4576-acc6-f07d4ddcbf52" />

---

## Folder Structure

interview_trainer/

├── assets/

│   ├── questions.json          ← Your question bank

│   ├── history.jsonl           ← All past attempts + scores

│   ├── grading_prompt.txt      ← Editable AI prompt template

├── main.py                     ← Main interview trainer

├── builder.py                  ← Question editor tool

├── .env                        ← OpenAI API key

├── run.bat                     ← Double-click to start

├── requirements.txt

└── README.md

---

## Installation

Enter this to the console to download all required lib: *pip install -r requirements.txt*

--- 

## Setup

### 1. **.env** file (in root folder) -> put your API key on this file
- OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

### 2. **grading_prompt.txt** (must contain these placeholders)

Question from category: <<QUESTION_CATEGORY>>
Question: <<QUESTION_TEXT>>
User answer: <<ANSWER_TEXT>>
<PROMPT CONTENT HERE>

### 3. **questions.json** example JSON Question Block

[
  {
    "qid": "1",
    "category": "Spark Architecture",
    "question": "What is the High-level Architecture of Spark?",
    "quick_answer": "Driver + Cluster Manager + Executors...",
    "short_answer": "Full detailed answer here...",
    "link": "https://spark.apache.org/docs/latest/"
  }
]

---

## How to Use

1. Start the Trainer: Double-click run.bat (or run python main.py)
2. Add/Edit Questions: run **builder.py** and enter the question content.

- Browse to your questions.json
- Fill fields (Question ID auto-assigns if blank)
- Click Save / Append

3. Practice

- Click New Question
- Type your answer
- Click SUBMIT → Get AI Feedback
- Use Retry This Question or Next Question

4. View History

- **Display History (All)**: To display the historical list of all submission, data retrived from *history.JSONL* file.
- **Display This Question**: Similiar to Display History, but this filters only that exact question.

---

## Keyboard Shortcuts

- Ctrl + Z → Undo in answer box
- Ctrl + V → Paste

---

## Troubleshooting

1. No questions appear

→ Check questions.json is a valid array and path is correct.

2. Feedback window looks broken

→ Resize the window slightly — it auto-adjusts.

3. API rate limit / cost

→ Using gpt-4o-mini (fast + very cheap).

---

## Author

Built by Hoang Anh Tuan

Hanoi, Vietnam

Feel free to customize the prompt, add more categories, or extend the history viewer.

Happy practicing!

May your next interview be a 10/10 🔥
