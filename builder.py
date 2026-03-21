import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, Toplevel
import json
import os

class QuestionBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Question Builder — Interview Bank")
        self.root.geometry("1000x780")
        self.root.minsize(800, 600)
        self.root.configure(bg="#f8f9fa")

        # Main frame with padding
        main_frame = tk.Frame(self.root, bg="#f8f9fa")
        main_frame.pack(fill="both", expand=True, padx=20, pady=15)

        # Top row: File selection
        file_frame = tk.Frame(main_frame, bg="#f8f9fa")
        file_frame.pack(fill="x", pady=(0, 10))

        tk.Label(file_frame, text="JSON file:", bg="#f8f9fa", font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
        self.file_var = tk.StringVar(value=os.path.join("assets", "questions.json"))
        tk.Entry(file_frame, textvariable=self.file_var, width=70, font=("Consolas", 10)).pack(side="left", fill="x", expand=True)
        tk.Button(file_frame, text="Browse", command=self.browse_file, width=10).pack(side="left", padx=8)
        tk.Button(file_frame, text="Load by ID", command=self.load_by_id, width=12).pack(side="left")
        self.load_id_entry = tk.Entry(file_frame, width=10, font=("Consolas", 10))
        self.load_id_entry.pack(side="left", padx=8)

        # Category & ID
        cat_id_frame = tk.Frame(main_frame, bg="#f8f9fa")
        cat_id_frame.pack(fill="x", pady=8)

        tk.Label(cat_id_frame, text="Category:", bg="#f8f9fa", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
        self.cat_entry = tk.Entry(cat_id_frame, font=("Segoe UI", 11))
        self.cat_entry.pack(side="left", fill="x", expand=True, padx=(0, 20))

        tk.Label(cat_id_frame, text="Question ID (auto if blank):", bg="#f8f9fa", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.qid_entry = tk.Entry(cat_id_frame, width=12, font=("Consolas", 11))
        self.qid_entry.pack(side="left", padx=8)

        # Question (made shorter)
        tk.Label(main_frame, text="Question:", bg="#f8f9fa", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))
        self.question_text = scrolledtext.ScrolledText(
            main_frame, height=2, font=("Segoe UI", 11), wrap="word", undo=True
        )
        self.question_text.pack(fill="x", expand=False, pady=4)

        # Quick Answer
        tk.Label(main_frame, text="Quick Answer (hint / bullet points):", bg="#f8f9fa", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 2))
        self.quick_text = scrolledtext.ScrolledText(
            main_frame, height=4, font=("Segoe UI", 11), wrap="word", undo=True
        )
        self.quick_text.pack(fill="x", expand=False, pady=4)

        # Short Answer
        tk.Label(main_frame, text="Short Answer (ideal / model answer):", bg="#f8f9fa", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 2))
        self.short_text = scrolledtext.ScrolledText(
            main_frame, height=7, font=("Segoe UI", 11), wrap="word", undo=True
        )
        self.short_text.pack(fill="x", expand=False, pady=4)

        # Link
        tk.Label(main_frame, text="Link (optional - https://...)", bg="#f8f9fa", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 2))
        self.link_entry = tk.Entry(main_frame, font=("Segoe UI", 11))
        self.link_entry.insert(0, "")
        self.link_entry.pack(fill="x", pady=4)

        # Buttons row (fixed at bottom)
        btn_frame = tk.Frame(main_frame, bg="#f8f9fa")
        btn_frame.pack(fill="x", pady=20)

        tk.Button(btn_frame, text="Preview JSON", command=self.preview_json, width=14).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Copy JSON", command=self.copy_json, width=12).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Save / Append", command=self.save_question, bg="#28a745", fg="white", font=("Segoe UI", 11, "bold"), width=16).pack(side="left", padx=12)
        tk.Button(btn_frame, text="New Block (Reset)", command=self.new_block, bg="#dc3545", fg="white", font=("Segoe UI", 11, "bold"), width=18).pack(side="left", padx=6)

        # JSON Preview
        tk.Label(main_frame, text="JSON Preview:", bg="#f8f9fa", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 2))
        self.preview_text = scrolledtext.ScrolledText(
            main_frame, height=10, font=("Consolas", 10), bg="#fdfdfd", state="disabled"
        )
        self.preview_text.pack(fill="both", expand=True, pady=4)

        self.questions = self.load_questions()
        self.root.mainloop()

    # ==================== REST OF THE CODE (unchanged) ====================

    def load_questions(self):
        path = self.file_var.get()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    else:
                        messagebox.showwarning("Format error", "File is not a JSON array.")
                        return []
            except Exception as e:
                messagebox.showerror("Load error", f"Cannot read JSON:\n{str(e)}")
                return []
        return []

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], initialdir="assets")
        if path:
            self.file_var.set(path)
            self.questions = self.load_questions()

    def get_next_available_id(self):
        if not self.questions:
            return "1"
        existing_ids = set()
        for q in self.questions:
            try:
                existing_ids.add(int(q["qid"]))
            except (ValueError, TypeError, KeyError):
                pass
        if not existing_ids:
            return "1"
        max_id = max(existing_ids)
        for i in range(1, max_id + 2):
            if i not in existing_ids:
                return str(i)
        return str(max_id + 1)

    def load_by_id(self):
        qid = self.load_id_entry.get().strip()
        if not qid:
            messagebox.showinfo("Info", "Enter ID to load.")
            return
        for q in self.questions:
            if str(q.get("qid")) == qid:
                self.cat_entry.delete(0, tk.END); self.cat_entry.insert(0, q.get("category", ""))
                self.qid_entry.delete(0, tk.END); self.qid_entry.insert(0, qid)
                self.question_text.delete("1.0", tk.END); self.question_text.insert("1.0", q.get("question", ""))
                self.quick_text.delete("1.0", tk.END); self.quick_text.insert("1.0", q.get("quick_answer", ""))
                self.short_text.delete("1.0", tk.END); self.short_text.insert("1.0", q.get("short_answer", ""))
                self.link_entry.delete(0, tk.END); self.link_entry.insert(0, q.get("link", ""))
                return
        messagebox.showinfo("Not found", f"No question with ID {qid}")

    def get_current_data(self):
        qid_input = self.qid_entry.get().strip()
        if not qid_input:
            qid = self.get_next_available_id()
            self.qid_entry.delete(0, tk.END)
            self.qid_entry.insert(0, qid)
        else:
            qid = qid_input

        return {
            "qid": qid,
            "category": self.cat_entry.get().strip(),
            "question": self.question_text.get("1.0", tk.END).strip(),
            "quick_answer": self.quick_text.get("1.0", tk.END).strip(),
            "short_answer": self.short_text.get("1.0", tk.END).strip(),
            "link": self.link_entry.get().strip()
        }

    def preview_json(self):
        data = self.get_current_data()
        preview_str = json.dumps(data, indent=2, ensure_ascii=False)

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", preview_str)
        self.preview_text.configure(state="disabled")

    def copy_json(self):
        self.preview_json()
        self.root.clipboard_clear()
        self.root.clipboard_append(self.preview_text.get("1.0", tk.END).strip())
        messagebox.showinfo("Copied", "JSON copied to clipboard.")

    def save_question(self):
        data = self.get_current_data()

        if not data["question"]:
            messagebox.showwarning("Missing", "Question text is required.")
            return

        path = self.file_var.get()
        if not path:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not path:
                return
            self.file_var.set(path)

        self.questions = self.load_questions()

        updated = False
        for i, q in enumerate(self.questions):
            if str(q.get("qid")) == data["qid"]:
                self.questions[i] = data
                updated = True
                break
        if not updated:
            self.questions.append(data)

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.questions, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", f"Saved question {data['qid']} to {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def new_block(self):
        self.qid_entry.delete(0, tk.END)
        self.cat_entry.delete(0, tk.END)
        self.question_text.delete("1.0", tk.END)
        self.quick_text.delete("1.0", tk.END)
        self.short_text.delete("1.0", tk.END)
        self.link_entry.delete(0, tk.END)
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.configure(state="disabled")

if __name__ == "__main__":
    QuestionBuilder()