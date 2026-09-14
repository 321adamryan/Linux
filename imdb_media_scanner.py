#!/usr/bin/env python3

import os
import re
import csv
import json
import tkinter as tk

from pathlib import Path
from tkinter import ttk, filedialog, messagebox


# ============================================================
# Configuration
# ============================================================

# Settings are saved here so your selected media folders
# remain available the next time you launch the program.
SETTINGS_FILE = Path.home() / ".imdb_media_scanner.json"


# Common media file extensions.
MEDIA_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
    ".m4v",
    ".wmv",
    ".ts",
    ".m2ts",
    ".mpg",
    ".mpeg",
    ".webm",
}


# IMDb ID pattern.
#
# Examples:
# tt1234567
# tt12345678
# tt123456789
#
# Case insensitive.
IMDB_PATTERN = re.compile(
    r"tt\d{7,10}",
    re.IGNORECASE
)


# Year pattern.
#
# Examples:
# (2015)
# [2015]
# 2015
YEAR_PATTERN = re.compile(
    r"(?:\(|\[)?((?:19|20)\d{2})(?:\)|\])?"
)


# Release tags that commonly appear after the title/year.
#
# These are primarily used when a filename doesn't use square
# brackets for every release tag.
RELEASE_TAG_PATTERN = re.compile(
    r"""
    \b
    (?:
        480p|
        576p|
        720p|
        1080p|
        1440p|
        2160p|
        4K|
        8K|
        UHD|
        BluRay|
        Bluray|
        BDRip|
        BRRip|
        WEBRip|
        WEB-DL|
        WEB|
        HDTV|
        DVDRip|
        DVD|
        HDR|
        HDR10|
        HDR10Plus|
        DolbyVision|
        DV|
        HEVC|
        H265|
        H264|
        X264|
        X265|
        AVC|
        AAC|
        AC3|
        EAC3|
        DTS|
        DTS-HD|
        TrueHD|
        Atmos|
        5\.1|
        7\.1|
        YTS|
        YTS\.MX|
        YIFY|
        PSA|
        RARBG|
        EZTV|
        AMZN|
        NF|
        Netflix|
        DSNP|
        Disney|
        HMAX|
        MAX|
        HBO|
        HULU|
        PCOK|
        Paramount|
        Peacock
    )
    \b
    """,
    re.IGNORECASE | re.VERBOSE
)


# ============================================================
# Application
# ============================================================

class IMDbScannerApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Media IMDb ID Scanner"
        )

        self.root.geometry(
            "850x650"
        )

        self.root.minsize(
            750,
            550
        )

        self.locations = []

        self.create_interface()

        self.load_settings()

    # ========================================================
    # Interface
    # ========================================================

    def create_interface(self):

        main_frame = ttk.Frame(
            self.root,
            padding=15
        )

        main_frame.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title = ttk.Label(
            main_frame,
            text="Media IMDb ID Scanner",
            font=(
                "TkDefaultFont",
                18,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            pady=(0, 5)
        )

        description = ttk.Label(
            main_frame,
            text=(
                "Finds media files that do not contain an IMDb ID "
                "anywhere in their folder or filename."
            ),
            wraplength=800
        )

        description.pack(
            anchor="w",
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # Root Locations
        # ----------------------------------------------------

        location_frame = ttk.LabelFrame(
            main_frame,
            text="Media Root Locations",
            padding=10
        )

        location_frame.pack(
            fill="both",
            expand=True
        )

        self.location_list = tk.Listbox(
            location_frame,
            height=8,
            selectmode=tk.EXTENDED
        )

        self.location_list.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        scrollbar = ttk.Scrollbar(
            location_frame,
            orient="vertical",
            command=self.location_list.yview
        )

        scrollbar.pack(
            side="left",
            fill="y"
        )

        self.location_list.config(
            yscrollcommand=scrollbar.set
        )

        button_frame = ttk.Frame(
            location_frame
        )

        button_frame.pack(
            side="right",
            fill="y"
        )

        ttk.Button(
            button_frame,
            text="Add Folder",
            command=self.add_location
        ).pack(
            fill="x",
            pady=(0, 5)
        )

        ttk.Button(
            button_frame,
            text="Remove Selected",
            command=self.remove_location
        ).pack(
            fill="x",
            pady=5
        )

        ttk.Button(
            button_frame,
            text="Clear All",
            command=self.clear_locations
        ).pack(
            fill="x",
            pady=5
        )

        # ----------------------------------------------------
        # File type options
        # ----------------------------------------------------

        file_frame = ttk.LabelFrame(
            main_frame,
            text="Scan Options",
            padding=10
        )

        file_frame.pack(
            fill="x",
            pady=15
        )

        self.media_only = tk.BooleanVar(
            value=True
        )

        ttk.Checkbutton(
            file_frame,
            text="Only scan common media files",
            variable=self.media_only
        ).pack(
            anchor="w"
        )

        ttk.Label(
            file_frame,
            text=(
                "Uncheck this if you want the scanner to examine "
                "every file."
            )
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        # ----------------------------------------------------
        # Scan
        # ----------------------------------------------------

        self.scan_button = ttk.Button(
            main_frame,
            text="Scan Media Library",
            command=self.start_scan
        )

        self.scan_button.pack(
            fill="x",
            pady=(0, 10)
        )

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        self.progress = ttk.Progressbar(
            main_frame,
            mode="indeterminate"
        )

        self.progress.pack(
            fill="x"
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_var = tk.StringVar(
            value="Ready to scan."
        )

        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var
        )

        status_label.pack(
            anchor="w",
            pady=(8, 5)
        )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        results_frame = ttk.LabelFrame(
            main_frame,
            text="Results",
            padding=10
        )

        results_frame.pack(
            fill="both",
            expand=True
        )

        self.results_text = tk.Text(
            results_frame,
            height=8,
            wrap="word"
        )

        self.results_text.pack(
            fill="both",
            expand=True
        )

        self.results_text.config(
            state="disabled"
        )

    # ========================================================
    # Settings
    # ========================================================

    def load_settings(self):

        if not SETTINGS_FILE.exists():
            return

        try:

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                settings = json.load(file)

            locations = settings.get(
                "locations",
                []
            )

            for location in locations:

                if os.path.isdir(location):

                    self.add_location_to_list(
                        location
                    )

        except Exception:
            pass

    def save_settings(self):

        settings = {
            "locations": self.locations
        }

        try:

            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    settings,
                    file,
                    indent=4
                )

        except Exception as error:

            print(
                f"Unable to save settings: {error}"
            )

    # ========================================================
    # Locations
    # ========================================================

    def add_location_to_list(
        self,
        location
    ):

        location = os.path.abspath(
            location
        )

        if location not in self.locations:

            self.locations.append(
                location
            )

            self.location_list.insert(
                tk.END,
                location
            )

        self.save_settings()

    def add_location(self):

        location = filedialog.askdirectory(
            title="Select Media Root Folder"
        )

        if location:

            self.add_location_to_list(
                location
            )

    def remove_location(self):

        selected = list(
            self.location_list.curselection()
        )

        for index in reversed(selected):

            location = self.location_list.get(
                index
            )

            self.location_list.delete(
                index
            )

            if location in self.locations:

                self.locations.remove(
                    location
                )

        self.save_settings()

    def clear_locations(self):

        self.location_list.delete(
            0,
            tk.END
        )

        self.locations.clear()

        self.save_settings()

    # ========================================================
    # Start Scan
    # ========================================================

    def start_scan(self):

        if not self.locations:

            messagebox.showwarning(
                "No Locations",
                "Please add at least one media root folder."
            )

            return

        output_file = filedialog.asksaveasfilename(
            title="Save IMDb Missing CSV",
            defaultextension=".csv",
            filetypes=[
                (
                    "CSV files",
                    "*.csv"
                ),
                (
                    "All files",
                    "*.*"
                )
            ],
            initialfile="missing_imdb_ids.csv"
        )

        if not output_file:

            return

        self.scan_button.config(
            state="disabled"
        )

        self.progress.start(
            10
        )

        self.results_text.config(
            state="normal"
        )

        self.results_text.delete(
            "1.0",
            tk.END
        )

        self.results_text.insert(
            tk.END,
            "Starting scan...\n\n"
        )

        self.results_text.config(
            state="disabled"
        )

        self.root.update_idletasks()

        try:

            results = self.scan_locations()

            self.write_csv(
                output_file,
                results
            )

            self.show_results(
                results,
                output_file
            )

        except Exception as error:

            messagebox.showerror(
                "Scan Error",
                str(error)
            )

        finally:

            self.progress.stop()

            self.scan_button.config(
                state="normal"
            )

    # ========================================================
    # Scan
    # ========================================================

    def scan_locations(self):

        results = []

        files_scanned = 0

        for root_location in self.locations:

            self.status_var.set(
                f"Scanning: {root_location}"
            )

            self.root.update_idletasks()

            for current_root, directories, files in os.walk(
                root_location,
                topdown=True,
                followlinks=False
            ):

                # Remove folders that cannot be read.
                directories[:] = [
                    directory
                    for directory in directories
                    if self.can_access_directory(
                        os.path.join(
                            current_root,
                            directory
                        )
                    )
                ]

                for filename in files:

                    full_path = os.path.join(
                        current_root,
                        filename
                    )

                    files_scanned += 1

                    if files_scanned % 100 == 0:

                        self.status_var.set(
                            f"Files scanned: {files_scanned} | "
                            f"Missing IMDb IDs: {len(results)}"
                        )

                        self.root.update_idletasks()

                    # ------------------------------------------------
                    # File extension
                    # ------------------------------------------------

                    extension = Path(
                        filename
                    ).suffix.lower()

                    if (
                        self.media_only.get()
                        and extension not in MEDIA_EXTENSIONS
                    ):

                        continue

                    # ------------------------------------------------
                    # IMDb ID detection
                    # ------------------------------------------------

                    if IMDB_PATTERN.search(
                        full_path
                    ):

                        continue

                    # ------------------------------------------------
                    # Create simplified reference name
                    # ------------------------------------------------

                    filename_without_extension = Path(
                        filename
                    ).stem

                    reference_name = self.create_reference_name(
                        filename_without_extension
                    )

                    # ------------------------------------------------
                    # Store result
                    # ------------------------------------------------

                    results.append({
                        "Full Path": full_path,
                        "Reference Name": reference_name
                    })

        # Sort alphabetically by full path.

        results.sort(
            key=lambda item: item["Full Path"].lower()
        )

        self.status_var.set(
            f"Scan complete. "
            f"{files_scanned} files scanned. "
            f"{len(results)} files without IMDb IDs."
        )

        return results

    # ========================================================
    # Reference Name
    # ========================================================

    @staticmethod
    def create_reference_name(
        filename
    ):
        """
        Converts a release-style filename into a simple
        title/year reference.

        Example:

        Attack On Titan (2015) [1080p] [BluRay] [5.1] [YTS.MX]

        becomes:

        Attack On Titan (2015)
        """

        name = filename.strip()

        # ----------------------------------------------------
        # Remove IMDb ID if one somehow exists in filename.
        # This normally won't happen because such files are
        # excluded from the scan.
        # ----------------------------------------------------

        name = IMDB_PATTERN.sub(
            "",
            name
        )

        # ----------------------------------------------------
        # Convert underscores and dots to spaces.
        #
        # Hyphens are NOT automatically converted because they
        # can legitimately occur in titles.
        # ----------------------------------------------------

        name = name.replace(
            "_",
            " "
        )

        # ----------------------------------------------------
        # Find year.
        # ----------------------------------------------------

        year_match = YEAR_PATTERN.search(
            name
        )

        if year_match:

            year = year_match.group(1)

            # Keep everything through the year.
            #
            # This means:
            #
            # Attack On Titan (2015) [1080p]
            #
            # becomes:
            #
            # Attack On Titan (2015)

            end_position = year_match.end()

            title_part = name[
                :end_position
            ]

            # Normalize whitespace.

            title_part = re.sub(
                r"\s+",
                " ",
                title_part
            ).strip()

            # Make sure the year has parentheses.

            if not title_part.endswith(
                f"({year})"
            ):

                title_part = re.sub(
                    rf"\s*[\[\(]?{year}[\]\)]?$",
                    f" ({year})",
                    title_part
                )

            return title_part.strip()

        # ----------------------------------------------------
        # No year found.
        #
        # Remove bracketed release tags.
        # ----------------------------------------------------

        name = re.sub(
            r"\[[^\]]*\]",
            "",
            name
        )

        # Remove common release tags.

        name = RELEASE_TAG_PATTERN.sub(
            "",
            name
        )

        # Normalize whitespace.

        name = re.sub(
            r"\s+",
            " ",
            name
        )

        return name.strip(
            " .-_"
        )

    # ========================================================
    # Directory Access
    # ========================================================

    @staticmethod
    def can_access_directory(
        directory
    ):

        try:

            return os.access(
                directory,
                os.R_OK
            )

        except Exception:

            return False

    # ========================================================
    # CSV
    # ========================================================

    @staticmethod
    def write_csv(
        output_file,
        results
    ):

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "Full Path",
                    "Reference Name"
                ]
            )

            writer.writeheader()

            writer.writerows(
                results
            )

    # ========================================================
    # Display Results
    # ========================================================

    def show_results(
        self,
        results,
        output_file
    ):

        self.results_text.config(
            state="normal"
        )

        self.results_text.delete(
            "1.0",
            tk.END
        )

        self.results_text.insert(
            tk.END,
            "Scan complete!\n\n"
        )

        self.results_text.insert(
            tk.END,
            f"Files scanned: "
            f"{self.status_var.get().split('|')[0].strip()}\n"
        )

        self.results_text.insert(
            tk.END,
            f"Files without IMDb IDs: "
            f"{len(results)}\n\n"
        )

        self.results_text.insert(
            tk.END,
            f"CSV saved to:\n"
            f"{output_file}\n\n"
        )

        if results:

            self.results_text.insert(
                tk.END,
                "First 25 results:\n\n"
            )

            for result in results[:25]:

                self.results_text.insert(
                    tk.END,
                    f"{result['Reference Name']}\n"
                    f"{result['Full Path']}\n\n"
                )

            if len(results) > 25:

                self.results_text.insert(
                    tk.END,
                    f"...and "
                    f"{len(results) - 25} more."
                )

        else:

            self.results_text.insert(
                tk.END,
                "Every scanned media file already "
                "contains an IMDb ID."
            )

        self.results_text.config(
            state="disabled"
        )

        messagebox.showinfo(
            "Scan Complete",
            f"Found {len(results)} files without IMDb IDs.\n\n"
            f"CSV saved to:\n{output_file}"
        )


# ============================================================
# Main
# ============================================================

def main():

    root = tk.Tk()

    IMDbScannerApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()
