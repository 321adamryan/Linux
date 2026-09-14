#!/usr/bin/env python3
import csv
from pathlib import Path
import re
import tkinter as tk
from tkinter import ttk, messagebox

CSV_PATH = Path.home() / "Desktop" / "missing_imdb_ids.csv"
TAG_RE = re.compile(r"\s*\[imdbid-[^\]]+\]", re.IGNORECASE)


def load_rows():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found:\n{CSV_PATH}")
    rows = []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for line, row in enumerate(reader, 1):
            if len(row) < 4:
                continue
            path_text, imdb = row[0].strip(), row[3].strip()
            if not path_text or not imdb:
                continue
            if not imdb.lower().startswith("tt"):
                imdb = "tt" + imdb
            rows.append((line, Path(path_text), imdb))
    return rows


def proposal(source, imdb):
    if not source.exists():
        return None, "SOURCE NOT FOUND"
    if TAG_RE.search(source.stem):
        return source, "ALREADY TAGGED"
    dest = source.with_name(f"{source.stem} [imdbid-{imdb}]{source.suffix}")
    if dest.exists():
        return dest, "DESTINATION EXISTS"
    return dest, "READY"


class App:
    def __init__(self, root, rows):
        self.root, self.rows = root, rows
        self.vars = []
        root.title("IMDb ID Filename Renamer")
        root.geometry("1400x750")

        top = ttk.Frame(root, padding=10); top.pack(fill="x")
        ttk.Label(top, text=f"CSV: {CSV_PATH}", font=(None, 10, "bold")).pack(anchor="w")
        ttk.Label(top, text="Uncheck files you do not want processed. Only READY files can be renamed.").pack(anchor="w", pady=(4, 8))

        controls = ttk.Frame(root, padding=(10, 0, 10, 8)); controls.pack(fill="x")
        ttk.Button(controls, text="Select All", command=self.select_all).pack(side="left")
        ttk.Button(controls, text="Select None", command=self.select_none).pack(side="left", padx=6)
        ttk.Button(controls, text="Reload CSV", command=self.reload).pack(side="left")
        self.count = ttk.Label(controls); self.count.pack(side="right")

        frame = ttk.Frame(root, padding=(10, 0, 10, 10)); frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame, highlightthickness=0)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y"); self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width))

        bottom = ttk.Frame(root, padding=10); bottom.pack(fill="x")
        self.status = ttk.Label(bottom); self.status.pack(side="left")
        ttk.Button(bottom, text="Rename Selected", command=self.rename).pack(side="right")
        self.build()

    def build(self):
        for w in self.inner.winfo_children(): w.destroy()
        self.vars = []
        headers = ["", "Status", "Current Path", "New Path"]
        for c, h in enumerate(headers):
            ttk.Label(self.inner, text=h, font=(None, 9, "bold")).grid(row=0, column=c, sticky="w", padx=5, pady=5)
        for r, (_, source, imdb) in enumerate(self.rows, 1):
            dest, status = proposal(source, imdb)
            var = tk.BooleanVar(value=status == "READY")
            self.vars.append(var)
            ttk.Checkbutton(self.inner, variable=var, command=self.update_count).grid(row=r, column=0, sticky="w", padx=5)
            ttk.Label(self.inner, text=status).grid(row=r, column=1, sticky="w", padx=5)
            ttk.Label(self.inner, text=str(source)).grid(row=r, column=2, sticky="w", padx=5)
            ttk.Label(self.inner, text=str(dest) if dest else "").grid(row=r, column=3, sticky="w", padx=5)
        for c in range(4): self.inner.grid_columnconfigure(c, weight=1)
        self.update_count()

    def update_count(self):
        self.count.config(text=f"{sum(v.get() for v in self.vars)} selected / {len(self.rows)} total")

    def select_all(self):
        for v, (_, source, imdb) in zip(self.vars, self.rows): v.set(proposal(source, imdb)[1] == "READY")
        self.update_count()

    def select_none(self):
        for v in self.vars: v.set(False)
        self.update_count()

    def reload(self):
        try:
            self.rows = load_rows(); self.build(); self.status.config(text="CSV reloaded.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def rename(self):
        selected = [x for v, x in zip(self.vars, self.rows) if v.get()]
        ready = []
        for _, source, imdb in selected:
            dest, status = proposal(source, imdb)
            if status == "READY": ready.append((source, dest))
        if not ready:
            messagebox.showinfo("Nothing to rename", "No selected files are currently READY.")
            return
        preview = "\n\n".join(f"{s}\n  → {d}" for s, d in ready[:15])
        if len(ready) > 15: preview += f"\n\n...and {len(ready)-15} more."
        if not messagebox.askyesno("Confirm Rename", f"Rename {len(ready)} selected file(s)?\n\n{preview}"):
            return
        ok, failures = 0, []
        for source, dest in ready:
            try: source.rename(dest); ok += 1
            except Exception as e: failures.append(f"{source}\n  {e}")
        log = CSV_PATH.with_name("missing_imdb_ids_rename_log.txt")
        log.write_text("IMDb Filename Rename Log\n" + "="*70 + f"\nSuccessful: {ok}\nFailures: {len(failures)}\n\n" + "\n\n".join(failures), encoding="utf-8")
        self.reload()
        messagebox.showwarning("Complete", f"Renamed: {ok}\nFailed: {len(failures)}\n\nLog:\n{log}") if failures else messagebox.showinfo("Complete", f"Renamed {ok} file(s).\n\nLog:\n{log}")


def main():
    try: rows = load_rows()
    except Exception as e:
        root = tk.Tk(); root.withdraw(); messagebox.showerror("Could not load CSV", str(e)); root.destroy(); return
    root = tk.Tk(); App(root, rows); root.mainloop()

if __name__ == "__main__": main()
