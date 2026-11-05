#!/usr/bin/env python3
"""Project a NRRD volume to an MP4 video from the CLI or a small GUI."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

from volume_projection import ProjectionApplication, ProjectionError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project NRRD planes to an MP4 video")
    parser.add_argument("nrrd", nargs="?", help="3-D NRRD volume path")
    parser.add_argument("csv", nargs="?", help="Plane definitions CSV path")
    parser.add_argument("mp4", nargs="?", help="Output MP4 video path")
    args = parser.parse_args(argv)
    used_gui = not all((args.nrrd, args.csv, args.mp4))

    if used_gui:
        selected = select_files(args.nrrd, args.csv, args.mp4)
        if selected is None:
            print("No input files were selected.", file=sys.stderr)
            return 1
        args.nrrd, args.csv, args.mp4 = selected

    output_path = Path(args.mp4).expanduser().resolve()
    try:
        count = ProjectionApplication().run(args.nrrd, args.csv, output_path)
    except ProjectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if used_gui:
            show_gui_message("Video creation failed", str(exc), error=True)
        return 1
    print(f"Created '{output_path}' with {count} frames")
    if used_gui:
        show_gui_message(
            "Video created",
            f"Created {count} frames.\n\nSaved to:\n{output_path}",
        )
    return 0


def show_gui_message(title: str, message: str, *, error: bool = False) -> None:
    """Show a result dialog when the program was started through the GUI."""
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        return

    try:
        root = tk.Tk()
        root.withdraw()
        if error:
            messagebox.showerror(title, message, parent=root)
        else:
            messagebox.showinfo(title, message, parent=root)
        root.destroy()
    except tk.TclError:
        # The terminal output remains available if a dialog cannot be shown.
        pass


def select_files(
    nrrd: str | None = None,
    csv: str | None = None,
    mp4: str | None = None,
) -> tuple[str, str, str] | None:
    """Open a form for selecting the volume, plane CSV, and output video."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError:
        print("Tkinter is unavailable; provide all three paths on the command line.", file=sys.stderr)
        return None

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Could not open the file-selection window: {exc}", file=sys.stderr)
        return None
    root.title("3D Volume Projection")
    root.resizable(False, False)

    values = {
        "nrrd": tk.StringVar(value=nrrd or ""),
        "csv": tk.StringVar(value=csv or ""),
        "mp4": tk.StringVar(value=mp4 or ""),
    }

    def browse(kind: str) -> None:
        if kind == "nrrd":
            path = filedialog.askopenfilename(
                title="Select NRRD volume",
                filetypes=[("NRRD files", "*.nrrd"), ("All files", "*.*")],
            )
        elif kind == "csv":
            path = filedialog.askopenfilename(
                title="Select plane definitions CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
        else:
            path = filedialog.asksaveasfilename(
                title="Choose output MP4",
                defaultextension=".mp4",
                filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")],
            )
        if path:
            values[kind].set(path)

    result: list[tuple[str, str, str] | None] = [None]

    def submit() -> None:
        selected = tuple(values[key].get().strip() for key in ("nrrd", "csv", "mp4"))
        if not all(selected):
            messagebox.showwarning("Missing file", "Please select all three files.", parent=root)
            return
        result[0] = cast(tuple[str, str, str], selected)
        root.destroy()

    fields = (
        ("NRRD volume:", "nrrd"),
        ("Plane CSV:", "csv"),
        ("Output MP4:", "mp4"),
    )
    for row, (label, kind) in enumerate(fields):
        tk.Label(root, text=label, anchor="w", width=16).grid(row=row, column=0, padx=8, pady=6)
        tk.Entry(root, textvariable=values[kind], width=55).grid(row=row, column=1, padx=4, pady=6)
        tk.Button(root, text="Browse...", command=lambda selected_kind=kind: browse(selected_kind)).grid(
            row=row, column=2, padx=8, pady=6
        )
    tk.Button(root, text="Create video", command=submit).grid(row=len(fields), column=1, pady=12)
    root.mainloop()
    return result[0]


if __name__ == "__main__":
    sys.exit(main())
