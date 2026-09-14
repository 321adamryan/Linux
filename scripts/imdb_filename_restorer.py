#!/usr/bin/env python3
import csv
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

CSV_PATH = Path.home() / "Desktop" / "missing_imdb_ids.csv"


def normalize_id(value):
    value = value.strip()
    if not value:
        return ""
    return value if value.lower().startswith("tt") else "tt" + value if value.isdigit() else value


def read_csv():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Could not find:\n{CSV_PATH}")
    rows = []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        for line, row in enumerate(csv.reader(f), 1):
            if len(row) < 4:
                continue
            original = row[0].strip()
            imdb_id = normalize_id(row[3])
            if original and imdb_id:
                rows.append((line, Path(original), imdb_id))
    return rows


def find_matches(original, imdb_id):
    if not original.parent.exists():
        return [], "DIRECTORY NOT FOUND"
    tag = f"[imdbid-{imdb_id}]".lower()
    try:
        matches = [p for p in original.parent.iterdir()
                   if p.is_file() and tag in p.name.lower()]
    except PermissionError:
        return [], "PERMISSION DENIED"
    if not matches:
        return [], "TAGGED FILE NOT FOUND"
    if len(matches) > 1:
        return matches, "MULTIPLE MATCHES"
    return matches, "READY"


class App:
    def __init__(self, root, rows):
        self.root = root
        self.rows = rows
        self.vars = []
        self.items = []
        root.title("IMDb Filename Restorer")
        root.geometry("1450x750")

        top = ttk.Frame(root, padding=10); top.pack(fill="x")
        ttk.Label(top, text="IMDb Filename Restorer", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        ttk.Label(top, text=f"CSV: {CSV_PATH}").pack(anchor="w", pady=3)
        ttk.Label(top, text="Only READY files are selected. Uncheck any file you do not want restored.").pack(anchor="w")

        controls = ttk.Frame(root, padding=(10, 0, 10, 8)); controls.pack(fill="x")
        ttk.Button(controls, text="Select All READY", command=self.select_all).pack(side="left")
        ttk.Button(controls, text="Select None", command=self.select_none).pack(side="left", padx=5)
        ttk.Button(controls, text="Refresh", command=self.refresh).pack(side="left")
        self.count = ttk.Label(controls); self.count.pack(side="right")

        outer = ttk.Frame(root, padding=10); outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, highlightthickness=0)
        bar = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y"); self.canvas.pack(side="left", fill="both", expand=True)
        self.frame = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))

        bottom = ttk.Frame(root, padding=10); bottom.pack(fill="x")
        self.status = ttk.Label(bottom); self.status.pack(side="left")
        ttk.Button(bottom, text="Restore Selected Files", command=self.restore).pack(side="right")
        self.build()

    def build(self):
        for w in self.frame.winfo_children(): w.destroy()
        self.vars.clear(); self.items.clear()
        for c, text in enumerate(["", "Status", "Current File", "Restore To"]):
            ttk.Label(self.frame, text=text, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=c, sticky="w", padx=5, pady=5)
        for r, (_, original, imdb_id) in enumerate(self.rows, 1):
            matches, status = find_matches(original, imdb_id)
            source = matches[0] if status == "READY" else None
            var = tk.BooleanVar(value=status == "READY")
            self.vars.append(var)
            self.items.append((source, original, imdb_id, status, matches))
            ttk.Checkbutton(self.frame, variable=var, command=self.update).grid(row=r, column=0, sticky="w", padx=5)
            ttk.Label(self.frame, text=status).grid(row=r, column=1, sticky="w", padx=5)
            current = str(source) if source else (f"{len(matches)} matches" if status == "MULTIPLE MATCHES" else "")
            ttk.Label(self.frame, text=current).grid(row=r, column=2, sticky="w", padx=5)
            ttk.Label(self.frame, text=str(original)).grid(row=r, column=3, sticky="w", padx=5)
        for c in range(4): self.frame.grid_columnconfigure(c, weight=1)
        self.update()

    def update(self):
        selected = sum(v.get() for v in self.vars)
        ready = sum(i[3] == "READY" for i in self.items)
        self.count.config(text=f"{selected} selected / {ready} READY / {len(self.items)} total")

    def select_all(self):
        for v, i in zip(self.vars, self.items): v.set(i[3] == "READY")
        self.update()

    def select_none(self):
        for v in self.vars: v.set(False)
        self.update()

    def refresh(self):
        try:
            self.rows = read_csv(); self.build(); self.status.config(text="Refreshed.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def restore(self):
        selected = [i for v, i in zip(self.vars, self.items) if v.get()]
        operations = []
        problems = []
        for _, original, imdb_id, _, _ in selected:
            matches, status = find_matches(original, imdb_id)
            if status != "READY":
                problems.append(f"{original} — {status}")
                continue
            source = matches[0]
            if original.exists():
                problems.append(f"{source}\nTarget already exists: {original}")
                continue
            operations.append((source, original))

        if not operations:
            messagebox.showwarning("Nothing to Restore", "No selected files are currently safe to restore.")
            return

        preview = "\n\n".join(f"{a}\n  → {b}" for a,b in operations[:20])
        if len(operations) > 20: preview += f"\n\n...and {len(operations)-20} more."
        extra = f"\n\nSkipped/problem rows: {len(problems)}" if problems else ""
        if not messagebox.askyesno("FINAL CONFIRMATION", f"Restore {len(operations)} file(s) to the exact names from Column A?\n\n{preview}{extra}\n\nContinue?"):
            return

        success, failures = 0, []
        for source, destination in operations:
            try:
                source.rename(destination); success += 1
            except Exception as e:
                failures.append(f"{source}\n→ {destination}\nERROR: {e}")

        log = CSV_PATH.with_name("missing_imdb_ids_restore_log.txt")
        with log.open("w", encoding="utf-8") as f:
            f.write("IMDb Filename Restore Log\n" + "="*80 + "\n")
            f.write(f"Successful: {success}\nFailures: {len(failures)}\nSkipped/problems: {len(problems)}\n\n")
            if failures: f.write("FAILURES\n" + "\n\n".join(failures) + "\n\n")
            if problems: f.write("SKIPPED / PROBLEMS\n" + "\n\n".join(problems) + "\n")
        self.refresh()
        messagebox.showwarning("Restore Complete", f"Successful: {success}\nFailures: {len(failures)}\nSkipped/problems: {len(problems)}\n\nLog: {log}") if failures or problems else messagebox.showinfo("Restore Complete", f"Successfully restored {success} file(s).\n\nLog: {log}")


def main():
    try: rows = read_csv()
    except Exception as e:
        root = tk.Tk(); root.withdraw(); messagebox.showerror("Could Not Load CSV", str(e)); root.destroy(); return
    root = tk.Tk(); App(root, rows); root.mainloop()

if __name__ == "__main__": main()
