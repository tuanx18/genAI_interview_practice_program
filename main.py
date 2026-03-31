import tkinter as tk
from tkinter import messagebox, Toplevel, Canvas, Scrollbar, Frame, Label, Button, simpledialog, ttk
import os
import random
import time
import re
import csv
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

# ==================== PICK QUESTION BUTTON (top-right) ====================
top_bar = Frame(root, bg="#f5f5f5")
top_bar.pack(fill="x", pady=(10, 0), padx=25)

Button(top_bar, 
       text="Pick a Question", 
       command=lambda: pick_question(),
       bg="#9b59b6", 
       fg="white", 
       font=("Segoe UI", 10, "bold"),
       width=18).pack(side="right")

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

def write_daily_csv(record):
    # Step 1 — Create output folder
    output_folder = os.path.join(BASE_DIR, "output")
    os.makedirs(output_folder, exist_ok=True)

    # Step 2 — Date format DDMMYYYY
    date_str = datetime.now().strftime("%d%m%Y")

    # Step 3 — Daily ID (fixed for now)
    daily_id = ""

    # Step 4 — Build filename
    file_name = f"itv_daily_{date_str}{daily_id}.csv"
    file_path = os.path.join(output_folder, file_name)

    # Step 5 — Select only required columns
    csv_row = [
        record["id"],
        record["submitted_at"],
        record["time_taken_minutes"],
        record["score"],
        record["question_id"]
    ]

    headers = [
        "id",
        "submitted_at",
        "time_taken_minutes",
        "score",
        "question_id"
    ]

    # Step 6 — Check if file exists
    file_exists = os.path.isfile(file_path)

    # Step 7 — Write CSV
    with open(file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header only once
        if not file_exists:
            writer.writerow(headers)

        # Append row
        writer.writerow(csv_row)

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
    header.pack(pady=5)

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
    body_frame.pack(pady=(0, 10))

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

def pick_question():
    # Filter only questions from currently selected categories
    pool = [q for q in questions if q["category"] in selected_categories]
    if not pool:
        messagebox.showinfo("No questions", "No questions available in your selected categories.")
        return

    # Sort by qid for nicer order
    pool.sort(key=lambda q: q["qid"])

    win = Toplevel(root)
    win.title("Pick a Question")
    win.geometry("920x520")
    win.configure(bg="#f5f5f5")
    win.resizable(True, True)

    Label(win, 
          text="Choose any question from your selected categories:",
          bg="#f5f5f5", 
          font=("Segoe UI", 12, "bold")).pack(pady=12)

    # Combobox with nice display
    combo_var = tk.StringVar()
    combo = ttk.Combobox(win, 
                         textvariable=combo_var, 
                         state="readonly", 
                         font=("Segoe UI", 10),
                         width=110)
    
    display_list = []
    qid_to_question = {}
    for q in pool:
        short_text = q["question"][:115] + ("..." if len(q["question"]) > 115 else "")
        display = f"Q{q['qid']} — {q['category']}: {short_text}"
        display_list.append(display)
        qid_to_question[display] = q

    combo['values'] = display_list
    combo.pack(padx=25, pady=8, fill="x")

    # Load selected question
    def load_selected():
        selected_display = combo_var.get()
        if not selected_display:
            messagebox.showwarning("Select", "Please choose a question.")
            return

        selected_q = qid_to_question[selected_display]

        # Replace current question
        global current_question, start_time
        current_question = selected_q

        question_label.config(text=current_question["question"])
        category_label.config(text=f"Category: {current_question['category']}")
        answer_text.delete("1.0", tk.END)
        start_time = time.time()
        update_timer()

        win.destroy()

    Button(win, 
           text="✅ Load This Question", 
           command=load_selected,
           bg="#27ae60", 
           fg="white", 
           font=("Segoe UI", 11, "bold")).pack(pady=20)

    # Bonus: Press Enter in combobox also loads
    combo.bind("<Return>", lambda e: load_selected())

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

        # ==================== ALWAYS APPEND NEW RECORD ====================
        history = []
        if os.path.exists(HISTORY_PATH):
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = [json.loads(line) for line in f]

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
        history.append(new_record)   # ← always store, never replace

        # Write daily
        write_daily_csv(new_record)

        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            for h in history:
                json.dump(h, f, ensure_ascii=False)
                f.write("\n")

        # ==================== FEEDBACK WINDOW WITH IMPROVED BOLD HEADERS ====================
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

        # === Rich text box ===
        text_box = tk.Text(fw, wrap="word", font=("Segoe UI", 11), bg="#fdfdfd", padx=10, pady=10)
        text_box.pack(fill="both", expand=True)

        # Tags
        text_box.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        text_box.tag_configure("ref_header", 
                               font=("Segoe UI", 11, "bold"), 
                               foreground="#2980b9")   # nice blueish color

        # Insert full text with new reference header
        display_text = comment + "\n\n--- Reference / Ideal short answer ---\n" + ideal
        text_box.insert("1.0", display_text)

        # 1. Apply bold to the new reference header
        pos = text_box.search("--- Reference / Ideal short answer ---", "1.0", nocase=True, stopindex="end")
        if pos:
            line_start = text_box.index(f"{pos} linestart")
            line_end   = text_box.index(f"{pos} lineend + 1 char")
            text_box.tag_add("ref_header", line_start, line_end)

        # Robust bolding: find any of the keywords (case-insensitive) and bold the whole line
        keywords = [
            "what i did good",
            "what you did good",
            "how can i",
            "bonus points if",
            "on my answer",
            "possible follow-up",
            "based on your",
            "short ideal"
        ]

        for kw in keywords:
            start_idx = "1.0"
            while True:
                pos = text_box.search(kw, start_idx, nocase=True, stopindex="end")
                if not pos:
                    break
                # Bold the entire line that contains the keyword
                line_start = text_box.index(f"{pos} linestart")
                line_end = text_box.index(f"{pos} lineend + 1 char")
                text_box.tag_add("bold", line_start, line_end)
                start_idx = line_end   # continue after this line

        text_box.config(state="disabled")

        # ==================== BUTTONS ====================
        def retry_same():
            fw.destroy()
            # Window closes → you can edit answer and submit again (new record will be saved)

        def next_q():
            fw.destroy()
            answered_set.add(current_question["qid"])
            load_new_question()

        Button(fw, text="Retry This Question",
               command=retry_same,
               bg="#f39c12", fg="white").pack(side="left", padx=15, pady=12)

        Button(fw, text="Next Question",
               command=next_q,
               bg="#27ae60", fg="white").pack(side="right", padx=15, pady=12)

    except Exception as e:
        messagebox.showerror("Error", str(e))

    finally:
        spinner_running = False
        submit_btn.config(state="normal", text="SUBMIT → Get AI Feedback")

load_new_question()
root.mainloop()