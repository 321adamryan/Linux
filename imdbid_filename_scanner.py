#!/usr/bin/env python3
import csv
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

TAG = re.compile(r"\[imdbid-(tt\d+)\]", re.I)
OUT = Path.home() / "Desktop" / "imdbid_filename_inventory.csv"
REPORT = Path.home() / "Desktop" / "imdbid_filename_inventory_report.txt"

def scan(folder):
    results, problems = [], []
    for path in Path(folder).rglob("*"):
        try:
            if not path.is_file() or "imdbid" not in path.name.lower():
                continue
            matches = TAG.findall(path.name)
            if len(matches) != 1:
                problems.append((str(path), "Malformed or multiple IMDb ID tags"))
                continue
            imdb = matches[0].lower()
            reference = TAG.sub("", path.stem).strip()
            reference = re.sub(r"\s+$", "", reference)
            results.append((str(path), reference, imdb))
        except (PermissionError, OSError) as e:
            problems.append((str(path), str(e)))
    return results, problems

def export_csv(results):
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Full Path", "Reference Name", "", "IMDb ID"])
        for full_path, reference, imdb in results:
            w.writerow([full_path, reference, "", imdb])

def write_report(results, problems, folder):
    ids = {}
    for full_path, reference, imdb in results:
        ids.setdefault(imdb, []).append(full_path)
    duplicates = {k:v for k,v in ids.items() if len(v) > 1}
    with REPORT.open("w", encoding="utf-8") as f:
        f.write("IMDb ID Filename Inventory Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Scanned folder: {folder}\n")
        f.write(f"Valid files: {len(results)}\n")
        f.write(f"Duplicate IMDb IDs: {len(duplicates)}\n")
        f.write(f"Problems: {len(problems)}\n\n")
        if duplicates:
            f.write("DUPLICATE IMDb IDs\n" + "-" * 80 + "\n")
            for imdb, paths in sorted(duplicates.items()):
                f.write(f"{imdb}\n")
                for path in paths:
                    f.write(f"  {path}\n")
                f.write("\n")
        if problems:
            f.write("PROBLEMS\n" + "-" * 80 + "\n")
            for path, reason in problems:
                f.write(f"{path}\n  {reason}\n\n")
    return duplicates

class App:
    def __init__(self, root):
        self.root = root
        root.title("IMDb ID Filename Scanner")
        root.geometry("1250x700")
        self.folder = None
        self.results = []
        self.problems = []
        self.duplicates = {}

        top = ttk.Frame(root, padding=12); top.pack(fill="x")
        ttk.Label(top, text="IMDb ID Filename Scanner",
                  font=("TkDefaultFont", 15, "bold")).pack(anchor="w")
        ttk.Label(top, text='Recursively finds filenames containing "[imdbid-tt1234567]"').pack(anchor="w", pady=4)

        controls = ttk.Frame(top); controls.pack(fill="x")
        ttk.Button(controls, text="Choose Folder", command=self.choose).pack(side="left")
        self.folder_label = ttk.Label(controls, text="No folder selected"); self.folder_label.pack(side="left", padx=12)
        self.scan_btn = ttk.Button(controls, text="Scan", command=self.do_scan, state="disabled"); self.scan_btn.pack(side="right")

        self.summary = ttk.Label(root, text="Choose a folder to begin.", padding=(12, 0, 12, 8)); self.summary.pack(fill="x")

        frame = ttk.Frame(root, padding=(12, 0, 12, 10)); frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=("path","name","id"), show="headings")
        for col, title, width in [("path","Full Path",650),("name","Reference Name",380),("id","IMDb ID",130)]:
            self.tree.heading(col, text=title); self.tree.column(col, width=width, anchor="w")
        sy = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y"); sx.pack(side="bottom", fill="x"); self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("duplicate", font=("TkDefaultFont", 9, "bold"))

        bottom = ttk.Frame(root, padding=12); bottom.pack(fill="x")
        self.status = ttk.Label(bottom, text=""); self.status.pack(side="left")
        self.export_btn = ttk.Button(bottom, text="Export CSV", command=self.export, state="disabled"); self.export_btn.pack(side="right")

    def choose(self):
        folder = filedialog.askdirectory(title="Choose folder to scan")
        if folder:
            self.folder = Path(folder)
            self.folder_label.config(text=str(self.folder))
            self.scan_btn.config(state="normal")
            self.status.config(text="Ready to scan.")

    def do_scan(self):
        self.scan_btn.config(state="disabled"); self.export_btn.config(state="disabled")
        self.status.config(text="Scanning...")
        self.root.update_idletasks()
        try:
            self.results, self.problems = scan(self.folder)
            self.duplicates = write_report(self.results, self.problems, self.folder)
            for x in self.tree.get_children(): self.tree.delete(x)
            for full_path, reference, imdb in self.results:
                self.tree.insert("", "end", values=(full_path, reference, imdb),
                                 tags=("duplicate",) if imdb in self.duplicates else ())
            self.summary.config(text=f"Found {len(self.results)} valid files | {len(self.duplicates)} duplicate IMDb IDs | {len(self.problems)} problems")
            self.export_btn.config(state="normal" if self.results else "disabled")
            self.status.config(text="Scan complete.")
        except Exception as e:
            messagebox.showerror("Scan Error", str(e))
            self.status.config(text="Scan failed.")
        finally:
            self.scan_btn.config(state="normal")

    def export(self):
        try:
            export_csv(self.results)
            msg = f"CSV created:\n\n{OUT}\n\nReport:\n{REPORT}"
            if self.duplicates:
                msg += f"\n\nWARNING: {len(self.duplicates)} duplicate IMDb IDs were found."
            messagebox.showinfo("Export Complete", msg)
            self.status.config(text=f"Exported {len(self.results)} rows.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

root = tk.Tk()
App(root)
root.mainloop()
