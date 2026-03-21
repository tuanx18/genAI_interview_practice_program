import tkinter as tk
from tkinter import messagebox, Toplevel, Canvas, Scrollbar, Frame, Label, Button, simpledialog
import os
import random
import time
import re
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import webbrowser
import matplotlib.pyplot as plt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==================== DEBUG TOGGLE ====================
DEBUG_MODE = True          # ← Change to False to stop printing to console

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
QUESTIONS_PATH = os.path.join(ASSETS_DIR, "questions.json")
HISTORY_PATH = os.path.join(ASSETS_DIR, "history.jsonl")
PROMPT_PATH = os.path.join(ASSETS_DIR, "grading_prompt.txt")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    GRADING_PROMPT_TEMPLATE = f.read()

# Load questions
def load_questions():
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

questions = load_questions()
categories = sorted({q["category"] for q in questions})
selected_categories = set(categories)
answered_set = set()

current_question = None
start_time = 0.0

root = tk.Tk()
root.title("Interview Trainer - AI Chatbot")
root.geometry("880x680")
root.configure(bg="#f5f5f5")

# UI elements
Label(root, text="Current Question:", bg="#f5f5f5", font=("Segoe UI", 12, "bold")).pack(pady=10)
question_label = Label(root, text="Click New Question to start", wraplength=820, justify="left", bg="white", relief="ridge", padx=15, pady=15, font=("Segoe UI", 11))
question_label.pack(pady=8, padx=25, fill="x")

category_label = Label(root, text="Category: —", bg="#f5f5f5", font=("Segoe UI", 10, "italic"), fg="#555")
category_label.pack(pady=(0, 8))

timer_label = Label(root, text="Time: 0:00", bg="#f5f5f5", font=("Segoe UI", 12))
timer_label.pack()

Label(root, text="Your Answer:", bg="#f5f5f5", font=("Segoe UI", 12, "bold")).pack(pady=5)
answer_text = tk.Text(root, height=14, font=("Segoe UI", 11), wrap="word")
answer_text.pack(padx=25, pady=10, fill="both", expand=True)

# Read More button (unchanged)
link_frame = Frame(root, bg="#f5f5f5")
link_frame.pack(pady=(0, 10))

def open_or_add_link():
    link = current_question.get("link", "").strip()
    if link and len(link) > 3 and (link.startswith("http://") or link.startswith("https://")):
        webbrowser.open(link)
    else:
        choice = messagebox.askyesno("No link found", "This question has no valid link.\nWould you like to add one now?")
        if choice:
            new_link = simpledialog.askstring("Add link", "Enter URL[](https://...):", parent=root)
            if new_link and (new_link.startswith("http://") or new_link.startswith("https://")):
                for q in questions:
                    if q["qid"] == current_question["qid"]:
                        q["link"] = new_link.strip()
                        break
                with open(QUESTIONS_PATH, "w", encoding="utf-8") as f:
                    json.dump(questions, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Saved", "Link added and saved.")
                current_question["link"] = new_link
            else:
                messagebox.showinfo("Cancelled", "No valid link entered.")

Button(link_frame, text="Read more →", command=open_or_add_link, bg="#8e44ad", fg="white", font=("Segoe UI", 10, "bold"), width=14).pack(side="left", padx=25)

btn_frame = Frame(root, bg="#f5f5f5")
btn_frame.pack(pady=12)

Button(btn_frame, text="Quit", command=root.quit, bg="#e74c3c", fg="white", width=10).pack(side="left", padx=5)
Button(btn_frame, text="New Question", command=lambda: load_new_question(), bg="#3498db", fg="white", width=14).pack(side="left", padx=5)
Button(btn_frame, text="Categories", command=lambda: open_categories(), bg="#2ecc71", fg="white", width=14).pack(side="left", padx=5)
Button(btn_frame, text="Reset Timer", command=lambda: reset_timer(), bg="#f39c12", fg="white", width=12).pack(side="left", padx=5)
submit_btn = Button(btn_frame, text="SUBMIT → Get AI Feedback", command=lambda: submit_answer(), bg="#27ae60", fg="white", font=("Segoe UI", 13, "bold"), width=22)
submit_btn.pack(side="left", padx=5)

Button(btn_frame, text="📋 History (All)", command=lambda: show_history(False)).pack(side="left", padx=5)
Button(btn_frame, text="📋 This Question", command=lambda: show_history(True)).pack(side="left", padx=5)

def update_timer():
    if not current_question: return
    elapsed = time.time() - start_time
    timer_label.config(text=f"Time: {int(elapsed//60)}:{int(elapsed%60):02d}")
    root.after(1000, update_timer)

def reset_timer():
    global start_time
    if current_question: start_time = time.time()

def load_new_question():
    global current_question, start_time
    pool = [q for q in questions if q["qid"] not in answered_set and q["category"] in selected_categories]
    if not pool:
        messagebox.showinfo("Done", "No more questions...")
        return
    current_question = random.choice(pool)
    question_label.config(text=current_question["question"])
    category_label.config(text=f"Category: {current_question['category']}")
    answer_text.delete("1.0", tk.END)
    start_time = time.time()
    update_timer()

# ================= LOADING SPINNER =================
spinner_running = False

def start_spinner():
    global spinner_running
    spinner_running = True
    animate_spinner()

def stop_spinner():
    global spinner_running
    spinner_running = False
    submit_btn.config(text="SUBMIT → Get AI Feedback")

def animate_spinner():
    if not spinner_running:
        return
    for c in "|/-\\":
        if not spinner_running:
            break
        submit_btn.config(text=f"Thinking... {c}")
        root.update()
        time.sleep(0.1)
    root.after(0, animate_spinner)

# ================= HISTORY CHART =================
# ================= HISTORY VIEW (TABLE VERSION) =================
def show_history(same_qid=False):
    if not os.path.exists(HISTORY_PATH):
        messagebox.showinfo("No data", "No history yet.")
        return

    records = []
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            if same_qid and data["question_id"] != current_question["qid"]:
                continue
            records.append(data)

    if not records:
        messagebox.showinfo("No data", "No matching history.")
        return

    # ---------- WINDOW ----------
    win = Toplevel(root)
    win.title("History Records" + (" (Same Question)" if same_qid else ""))
    win.geometry("760x520")
    win.configure(bg="#f5f5f5")

    # ---------- SORT ----------
    sort_frame = Frame(win, bg="#f5f5f5")
    sort_frame.pack(pady=8)

    sort_key_var = tk.StringVar(value="id")
    order_var = tk.StringVar(value="asc")

    def apply_sort():
        key = sort_key_var.get()
        reverse = order_var.get() == "desc"

        if key == "time":
            records.sort(key=lambda x: x["time_taken_minutes"], reverse=reverse)
        elif key == "score":
            records.sort(key=lambda x: x["score"], reverse=reverse)
        else:
            records.sort(key=lambda x: x["id"], reverse=reverse)

        render_rows()

    options = ["score", "time"]
    if not same_qid:
        options.insert(0, "id")

    Label(sort_frame, text="Sort by:", bg="#f5f5f5").pack(side="left")
    tk.OptionMenu(sort_frame, sort_key_var, *options).pack(side="left", padx=5)
    tk.OptionMenu(sort_frame, order_var, "asc", "desc").pack(side="left", padx=5)
    Button(sort_frame, text="Apply", command=apply_sort).pack(side="left", padx=5)

    # ---------- HEADER (PINNED) ----------
    header = Frame(win, bg="#dfe6e9")
    header.pack(fill="x", padx=10)

    def header_label(text, width):
        return Label(header, text=text, width=width, bg="#dfe6e9",
                     font=("Segoe UI", 10, "bold"), anchor="w")

    header_label("ID", 6).pack(side="left")
    if not same_qid:
        header_label("QID", 8).pack(side="left")
    header_label("Score", 10).pack(side="left")
    header_label("Time (min)", 12).pack(side="left")
    header_label("Date", 14).pack(side="left")

    # ---------- SCROLLABLE BODY ----------
    body_frame = Frame(win)
    body_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    canvas = Canvas(body_frame, bg="#ffffff", highlightthickness=0)
    scrollbar = Scrollbar(body_frame, orient="vertical", command=canvas.yview)
    table_frame = Frame(canvas, bg="#ffffff")

    table_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=table_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ---------- RENDER ----------
    def render_rows():
        for w in table_frame.winfo_children():
            w.destroy()

        for r in records:
            row = Frame(table_frame, bg="#ffffff")
            row.pack(fill="x")

            def cell(text, width, fg="#2c3e50", bold=False):
                font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
                Label(row, text=text, width=width, anchor="w",
                      bg="#ffffff", fg=fg, font=font).pack(side="left")

            cell(r["id"], 6)

            if not same_qid:
                cell(r["question_id"], 8)

            # Score styling
            is_good = r["score"] >= 8
            cell(f"{r['score']}", 10,
                 fg="#27ae60" if is_good else "#2c3e50",
                 bold=is_good)

            cell(f"{r['time_taken_minutes']}", 12)
            cell(r["submitted_at"], 14)

    # default sort
    records.sort(key=lambda x: x["id"])
    render_rows()

# ================= RETRY FEATURE =================
def retry_last(question, user_answer):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": question}],
            temperature=0.7
        )
        content = resp.choices[0].message.content.strip()

        match = re.search(r"([0-9]*\.?[0-9]+)", content)
        score = float(match.group(1)) if match else 0.0

        # overwrite last line
        lines = []
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if lines:
            last = json.loads(lines[-1])
            last["score"] = score
            last["generated_comment"] = content

            lines[-1] = json.dumps(last, ensure_ascii=False) + "\n"

            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                f.writelines(lines)

        messagebox.showinfo("Updated", "Last attempt replaced!")

    except Exception as e:
        messagebox.showerror("Retry Error", str(e))

def open_categories():
    top = Toplevel(root)
    top.title("Select Categories")
    top.geometry("380x500")
    vars_dict = {}
    for cat in categories:
        var = tk.BooleanVar(value=cat in selected_categories)
        cnt = sum(1 for q in questions if q["category"] == cat)
        tk.Checkbutton(top, text=f"{cat} ({cnt} questions)", variable=var).pack(anchor="w", padx=30)
        vars_dict[cat] = var
    def apply():
        global selected_categories
        selected_categories = {c for c, v in vars_dict.items() if v.get()}
        top.destroy()
        load_new_question()
    Button(top, text="Apply", command=apply, bg="#27ae60", fg="white").pack(pady=20)

def submit_answer():
    global current_question

    if not current_question:
        messagebox.showwarning("No question", "Load a question first!")
        return

    user_answer = answer_text.get("1.0", tk.END).strip()
    if not user_answer:
        messagebox.showwarning("Empty", "Please write your answer.")
        return

    elapsed_min = round((time.time() - start_time) / 60, 2)

    prompt = GRADING_PROMPT_TEMPLATE.replace("<<QUESTION_TEXT>>", current_question["question"]) \
                                   .replace("<<ANSWER_TEXT>>", user_answer) \
                                   .replace("<<QUESTION_CATEGORY>>", current_question.get("category", "General"))

    if DEBUG_MODE:
        print("\n" + "="*90)
        print("PROMPT SENT TO GPT:")
        print(prompt)
        print("="*90 + "\n")

    # ==================== SPINNER ====================
    spinner_running = True
    spinner_states = ["Thinking   ", "Thinking.  ", "Thinking.. ", "Thinking..."]

    def animate_spinner(i=0):
        if spinner_running:
            submit_btn.config(text=spinner_states[i % len(spinner_states)])
            root.after(300, animate_spinner, i+1)

    submit_btn.config(state="disabled")
    animate_spinner()
    root.update()

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7
        )
        content = resp.choices[0].message.content.strip()

        if DEBUG_MODE:
            print("\nGPT RESPONSE:\n" + content + "\n")

        # ==================== SCORE PARSE ====================
        score = 0.0
        comment = content
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if line.strip().lower().startswith("score:"):
                m = re.search(r"([0-9]*\.?[0-9]+)", line)
                if m:
                    try:
                        score = float(m.group(1))
                    except:
                        score = 0.0
                comment = "\n".join(lines[i+1:]).strip()
                break

        ideal = current_question.get("short_answer") or current_question.get("Short Answer", "")

        # ==================== LOAD HISTORY ====================
        history = []
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = [json.loads(line) for line in f]

        # ==================== CHECK SAME QID ====================
        existing_index = None
        for i, h in enumerate(history):
            if h["question_id"] == current_question["qid"]:
                existing_index = i
                break

        new_record = {
            "id": len(history) + 1,
            "submitted_at": datetime.now().strftime("%d/%m/%Y"),
            "time_taken_minutes": elapsed_min,
            "score": score,
            "question_id": current_question["qid"],
            "my_answer": user_answer,
            "generated_comment": comment,
            "ideal_answer": ideal
        }

        # ==================== SAVE LOGIC ====================
        if existing_index is not None:
            replace = messagebox.askyesno(
                "Retry detected",
                "You already answered this question.\nDo you want to REPLACE the old attempt?"
            )
            if replace:
                history[existing_index] = new_record
            else:
                history.append(new_record)
        else:
            history.append(new_record)

        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            for h in history:
                json.dump(h, f, ensure_ascii=False)
                f.write("\n")

        # ==================== FEEDBACK WINDOW ====================
        fw = Toplevel(root)
        fw.title("AI Feedback")
        fw.geometry("860x640")
        fw.configure(bg="#fdfdfd")

        Label(fw, text=current_question["question"],
              font=("Segoe UI", 11, "italic"),
              bg="#ecf0f1").pack(fill="x", padx=10, pady=5)

        color = "#27ae60" if score >= 8 else "#e67e22" if score >= 5.5 else "#c0392b"

        Label(fw, text=f"Score: {score:.1f}/10",
              font=("Segoe UI", 20, "bold"),
              fg=color, bg="#fdfdfd").pack(pady=10)

        # ==================== COMMENT ====================
        text_box = tk.Text(fw, wrap="word", font=("Segoe UI", 11))
        text_box.insert("1.0", comment + "\n\n--- Reference ---\n" + ideal)
        text_box.config(state="disabled")
        text_box.pack(fill="both", expand=True, padx=10, pady=10)

        # ==================== BUTTONS ====================
        def retry_same():
            fw.destroy()

        def next_q():
            fw.destroy()
            answered_set.add(current_question["qid"])
            load_new_question()

        Button(fw, text="Retry This Question",
               command=retry_same,
               bg="#f39c12", fg="white").pack(side="left", padx=10, pady=10)

        Button(fw, text="Next Question",
               command=next_q,
               bg="#27ae60", fg="white").pack(side="right", padx=10, pady=10)

    except Exception as e:
        messagebox.showerror("Error", str(e))

    finally:
        spinner_running = False
        submit_btn.config(state="normal", text="SUBMIT → Get AI Feedback")

load_new_question()
root.mainloop()