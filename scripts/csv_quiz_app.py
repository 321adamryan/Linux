import csv
import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

# ============================================================
# QUIZ APP COLOR THEME
# ============================================================
APP_BG = "#111184"       # Entire application background
CARD_BG = "#10144A"      # Question and answer rectangle background
CARD_BORDER = "#0D18D1"  # Question and answer rectangle border
TEXT_COLOR = "#FFFFFF"   # White text
BUTTON_BG = "#10144A"
BUTTON_ACTIVE = "#2E4A5E"

REQUIRED_HEADERS = [
    "ID", "Question", "Correct Answer",
    "Potential Answer 1", "Potential Answer 2",
    "Potential Answer 3", "Potential Answer 4",
]


class RoundedCard(tk.Canvas):
    def __init__(self, parent, text="", variable=None, value=None,
                 selectable=False, width=700, height=64, radius=18,
                 fill=CARD_BG, outline=CARD_BORDER, outline_width=2,
                 font=("Arial", 13), padding=18, **kwargs):
        super().__init__(
            parent, width=width, height=height, bg=APP_BG,
            highlightthickness=0, bd=0, **kwargs
        )
        self.card_width = width
        self.card_height = height
        self.radius = radius
        self.fill = fill
        self.outline = outline
        self.outline_width = outline_width
        self.text = text
        self.variable = variable
        self.value = value
        self.selectable = selectable
        self.font = font
        self.padding = padding

        self.bind("<Button-1>", self.on_click)
        self.draw()

        if self.variable is not None:
            self.variable.trace_add("write", self.on_variable_change)

    def rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
        ]
        return self.create_polygon(
            points, smooth=True, splinesteps=36, **kwargs
        )

    def draw(self):
        self.delete("all")

        selected = (
            self.selectable and self.variable is not None
            and self.variable.get() == self.value
        )

        border = TEXT_COLOR if selected else self.outline
        border_width = 3 if selected else self.outline_width

        self.rounded_rectangle(
            2, 2, self.card_width - 2, self.card_height - 2,
            self.radius, fill=self.fill, outline=border,
            width=border_width
        )

        if self.selectable:
            cx = 28
            cy = self.card_height // 2

            self.create_oval(
                cx - 9, cy - 9, cx + 9, cy + 9,
                outline=TEXT_COLOR, width=2, fill=self.fill
            )

            if selected:
                self.create_oval(
                    cx - 4, cy - 4, cx + 4, cy + 4,
                    outline=TEXT_COLOR, fill=TEXT_COLOR
                )

            text_x = 52
            anchor = "w"
            justify = "left"
            text_width = self.card_width - 90
        else:
            text_x = self.card_width // 2
            anchor = "center"
            justify = "center"
            text_width = self.card_width - 50

        self.create_text(
            text_x, self.card_height // 2,
            text=self.text, fill=TEXT_COLOR, font=self.font,
            width=text_width, anchor=anchor, justify=justify
        )

    def on_click(self, event=None):
        if self.selectable and self.variable is not None:
            self.variable.set(self.value)

    def on_variable_change(self, *args):
        self.draw()


class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Quiz App")
        self.root.geometry("920x700")
        self.root.minsize(780, 560)
        self.root.configure(bg=APP_BG)

        self.csv_path = None
        self.quiz_name = ""
        self.questions = []
        self.current_index = 0
        self.results = []

        self.selected_answer = tk.StringVar()
        self.shuffle_questions = tk.BooleanVar(value=False)
        self.shuffle_answers = tk.BooleanVar(value=True)

        self.build_start_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def styled_button(self, parent, text, command, width=20):
        return tk.Button(
            parent, text=text, command=command,
            font=("Arial", 12, "bold"),
            width=width, height=2,
            bg=BUTTON_BG, fg=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat", bd=0, cursor="hand2",
            highlightthickness=1,
            highlightbackground=CARD_BORDER
        )

    def styled_checkbutton(self, parent, text, variable):
        return tk.Checkbutton(
            parent, text=text, variable=variable,
            font=("Arial", 11),
            bg=APP_BG, fg=TEXT_COLOR,
            activebackground=APP_BG,
            activeforeground=TEXT_COLOR,
            selectcolor=CARD_BG,
            highlightthickness=0, bd=0
        )

    def build_start_screen(self):
        self.clear_window()

        container = tk.Frame(self.root, bg=APP_BG)
        container.pack(expand=True, fill="both", padx=40, pady=30)

        tk.Label(
            container, text="CSV Quiz App",
            font=("Arial", 26, "bold"),
            bg=APP_BG, fg=TEXT_COLOR
        ).pack(pady=(35, 15))

        tk.Label(
            container,
            text=(
                "Select a CSV file containing these columns:\n\n"
                "ID\n"
                "Question\n"
                "Correct Answer\n"
                "Potential Answer 1\n"
                "Potential Answer 2\n"
                "Potential Answer 3\n"
                "Potential Answer 4"
            ),
            font=("Arial", 12), justify="center",
            wraplength=760, bg=APP_BG, fg=TEXT_COLOR
        ).pack(pady=10)

        options = tk.Frame(container, bg=APP_BG)
        options.pack(pady=20)

        self.styled_checkbutton(
            options, "Shuffle question order",
            self.shuffle_questions
        ).pack(anchor="w", pady=5)

        self.styled_checkbutton(
            options, "Shuffle answer choices",
            self.shuffle_answers
        ).pack(anchor="w", pady=5)

        self.styled_button(
            container, "Select Quiz CSV",
            self.select_csv, 22
        ).pack(pady=25)

    def select_csv(self):
        path = filedialog.askopenfilename(
            title="Select Quiz CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)

                if reader.fieldnames is None:
                    raise ValueError("The CSV does not contain a header row.")

                missing = [
                    h for h in REQUIRED_HEADERS
                    if h not in reader.fieldnames
                ]

                if missing:
                    raise ValueError(
                        "Missing required column(s):\n" + "\n".join(missing)
                    )

                questions = []

                for row_number, row in enumerate(reader, start=2):
                    q = {
                        h: (row.get(h) or "").strip()
                        for h in REQUIRED_HEADERS
                    }

                    if not q["Question"]:
                        continue

                    if not q["Correct Answer"]:
                        raise ValueError(
                            f"Row {row_number} has no Correct Answer."
                        )

                    answers = [
                        q["Potential Answer 1"],
                        q["Potential Answer 2"],
                        q["Potential Answer 3"],
                        q["Potential Answer 4"],
                    ]
                    answers = [a for a in answers if a]

                    if q["Correct Answer"] not in answers:
                        answers.append(q["Correct Answer"])

                    if len(answers) < 2:
                        raise ValueError(
                            f"Row {row_number} needs at least two answers."
                        )

                    q["_answers"] = answers
                    questions.append(q)

            if not questions:
                raise ValueError("No usable questions were found.")

            self.csv_path = path
            self.quiz_name = os.path.splitext(os.path.basename(path))[0]
            self.questions = questions

            if self.shuffle_questions.get():
                random.shuffle(self.questions)

            self.current_index = 0
            self.results = []
            self.show_question()

        except Exception as exc:
            messagebox.showerror("Unable to Load Quiz", str(exc))

    def get_live_score(self):
        """Return correct answers and percent based on the full quiz.

        The quiz begins at 100%. Each incorrect answer removes that
        question's share of the total possible score.
        """
        total_questions = len(self.questions)

        if total_questions == 0:
            return 0, 100.0

        incorrect = sum(
            1 for result in self.results
            if result["Result"] == "Incorrect"
        )

        correct = len(self.results) - incorrect
        percentage = ((total_questions - incorrect) / total_questions) * 100

        return correct, percentage

    def show_question(self):
        self.clear_window()
        question = self.questions[self.current_index]

        container = tk.Frame(self.root, bg=APP_BG)
        container.pack(expand=True, fill="both", padx=28, pady=(28, 18))

        # ------------------------------------------------------------
        # LIVE SCORE HEADER
        # Starts at 100% and decreases only when an answer is wrong.
        # ------------------------------------------------------------
        correct_so_far, live_percentage = self.get_live_score()

        score_header = tk.Frame(container, bg=APP_BG)
        score_header.pack(fill="x", padx=8, pady=(0, 18))

        tk.Label(
            score_header,
            text=f"Score: {correct_so_far}/{len(self.questions)}",
            font=("Arial", 13, "bold"),
            bg=APP_BG,
            fg=TEXT_COLOR
        ).pack(side="left")

        tk.Label(
            score_header,
            text=f"{live_percentage:.1f}%",
            font=("Arial", 13, "bold"),
            bg=APP_BG,
            fg=TEXT_COLOR
        ).pack(side="right")

        tk.Label(
            container, text=self.quiz_name,
            font=("Arial", 22, "bold"),
            bg=APP_BG, fg=TEXT_COLOR
        ).pack(pady=(8, 4))

        tk.Label(
            container,
            text=f"Question {self.current_index + 1} of {len(self.questions)}",
            font=("Arial", 11),
            bg=APP_BG, fg=TEXT_COLOR
        ).pack(pady=(0, 15))

        RoundedCard(
            container, text=question["Question"],
            width=820, height=110, radius=22,
            font=("Arial", 16, "bold")
        ).pack(pady=(8, 20))

        self.selected_answer.set("")

        answers = list(question["_answers"])
        if self.shuffle_answers.get():
            random.shuffle(answers)

        answer_frame = tk.Frame(container, bg=APP_BG)
        answer_frame.pack(pady=5)

        for answer in answers:
            RoundedCard(
                answer_frame, text=answer,
                variable=self.selected_answer,
                value=answer, selectable=True,
                width=790, height=72, radius=18,
                font=("Arial", 13)
            ).pack(pady=7)

        button_text = (
            "Finish Quiz"
            if self.current_index == len(self.questions) - 1
            else "Next Question"
        )

        self.styled_button(
            container, button_text,
            self.submit_answer, 18
        ).pack(pady=22)

    def submit_answer(self):
        selected = self.selected_answer.get()

        if not selected:
            messagebox.showwarning(
                "Select an Answer",
                "Please select an answer before continuing."
            )
            return

        q = self.questions[self.current_index]

        result = {
            "ID": q["ID"],
            "Question": q["Question"],
            "Correct Answer": q["Correct Answer"],
            "Potential Answer 1": q["Potential Answer 1"],
            "Potential Answer 2": q["Potential Answer 2"],
            "Potential Answer 3": q["Potential Answer 3"],
            "Potential Answer 4": q["Potential Answer 4"],
            "Selected Answer": selected,
            "Result": (
                "Correct"
                if selected == q["Correct Answer"]
                else "Incorrect"
            )
        }

        self.results.append(result)
        self.current_index += 1

        if self.current_index < len(self.questions):
            self.show_question()
        else:
            self.show_results()

    def show_results(self):
        self.clear_window()

        total = len(self.results)
        correct = sum(r["Result"] == "Correct" for r in self.results)
        incorrect = total - correct
        percentage = correct / total * 100 if total else 0

        container = tk.Frame(self.root, bg=APP_BG)
        container.pack(expand=True, fill="both", padx=40, pady=30)

        tk.Label(
            container, text=self.quiz_name,
            font=("Arial", 22, "bold"),
            bg=APP_BG, fg=TEXT_COLOR
        ).pack(pady=(25, 12))

        tk.Label(
            container, text="Quiz Complete",
            font=("Arial", 20, "bold"),
            bg=APP_BG, fg=TEXT_COLOR
        ).pack(pady=8)

        summary = (
            f"Score: {correct} / {total}\n"
            f"Correct: {correct}\n"
            f"Incorrect: {incorrect}\n"
            f"Percentage: {percentage:.1f}%"
        )

        RoundedCard(
            container, text=summary,
            width=500, height=170, radius=24,
            font=("Arial", 16, "bold")
        ).pack(pady=24)

        buttons = tk.Frame(container, bg=APP_BG)
        buttons.pack(pady=12)

        self.styled_button(
            buttons, "Export Results CSV",
            self.export_results
        ).grid(row=0, column=0, padx=10, pady=8)

        self.styled_button(
            buttons, "Choose Another Quiz",
            self.build_start_screen
        ).grid(row=0, column=1, padx=10, pady=8)

        self.styled_button(
            buttons, "Retake Same Quiz",
            self.retake_quiz
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=8)

    def retake_quiz(self):
        if self.shuffle_questions.get():
            random.shuffle(self.questions)

        self.current_index = 0
        self.results = []
        self.show_question()

    def export_results(self):
        if not self.results:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"{self.quiz_name}_results_{timestamp}.csv"

        path = filedialog.asksaveasfilename(
            title="Save Quiz Results",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        total = len(self.results)
        correct = sum(r["Result"] == "Correct" for r in self.results)
        percent = correct / total * 100 if total else 0

        fields = [
            "Quiz Name", "Quiz Date", "Score", "Score Percent",
            "ID", "Question", "Correct Answer",
            "Potential Answer 1", "Potential Answer 2",
            "Potential Answer 3", "Potential Answer 4",
            "Selected Answer", "Result"
        ]

        quiz_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()

                for result in self.results:
                    writer.writerow({
                        "Quiz Name": self.quiz_name,
                        "Quiz Date": quiz_date,
                        "Score": f"{correct}/{total}",
                        "Score Percent": f"{percent:.1f}%",
                        **result
                    })

            messagebox.showinfo(
                "Results Exported",
                f"Results saved successfully:\n\n{path}"
            )

        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    QuizApp(root)
    root.mainloop()
