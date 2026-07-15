from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from .demoparser_extractor import Demoparser2Extractor
from .overlay import build_overlay_paths
from .svg_renderer import render_overlay_svg


def launch_gui(default_demos_dir: str | Path | None = None) -> None:
    demos_dir = Path(default_demos_dir or Path(__file__).resolve().parent / "demos")
    demos_dir.mkdir(parents=True, exist_ok=True)

    root = tk.Tk()
    root.title("CS Overlay")
    root.geometry("760x440")

    tk.Label(root, text=f"Demos folder: {demos_dir}", anchor="w").pack(fill="x", padx=12, pady=(12, 4))
    tk.Label(root, text="Select one or more demos").pack(anchor="w", padx=12)

    listbox = tk.Listbox(root, selectmode=tk.MULTIPLE, width=100, height=12)
    listbox.pack(fill="both", expand=True, padx=12, pady=8)

    demo_files = sorted(demos_dir.glob("*.dem"))
    if not demo_files:
        listbox.insert(tk.END, "No .dem files found in demos folder.")
        listbox.configure(state=tk.DISABLED)
    else:
        for demo_file in demo_files:
            listbox.insert(tk.END, demo_file.name)

    controls = tk.Frame(root)
    controls.pack(fill="x", padx=12, pady=8)

    player_var = tk.StringVar()
    side_var = tk.StringVar()
    title_var = tk.StringVar(value="CS Demo Overlay")
    output_var = tk.StringVar(value=str(Path.cwd() / "overlay.svg"))

    tk.Label(controls, text="Player").grid(row=0, column=0, sticky="w")
    tk.Entry(controls, textvariable=player_var, width=24).grid(row=0, column=1, padx=(0, 14))
    tk.Label(controls, text="Side (CT/T)").grid(row=0, column=2, sticky="w")
    tk.Entry(controls, textvariable=side_var, width=10).grid(row=0, column=3, padx=(0, 14))
    tk.Label(controls, text="Title").grid(row=0, column=4, sticky="w")
    tk.Entry(controls, textvariable=title_var, width=26).grid(row=0, column=5)

    tk.Label(controls, text="Output SVG").grid(row=1, column=0, sticky="w", pady=(8, 0))
    tk.Entry(controls, textvariable=output_var, width=60).grid(row=1, column=1, columnspan=5, sticky="we", pady=(8, 0))

    def render_selected() -> None:
        selected = listbox.curselection()
        if not selected or not demo_files:
            messagebox.showerror("No demos selected", "Pick at least one .dem file.")
            return

        selected_paths = [str(demo_files[index]) for index in selected]
        labels = [Path(path).stem for path in selected_paths]
        side = side_var.get().strip().upper() or None
        if side not in {None, "CT", "T"}:
            messagebox.showerror("Invalid side", "Side must be CT or T.")
            return

        try:
            paths = build_overlay_paths(
                demo_paths=selected_paths,
                extractor=Demoparser2Extractor(),
                player_name=player_var.get().strip() or None,
                side=side,
                labels=labels,
                min_points=2,
            )
            svg = render_overlay_svg(paths=paths, title=title_var.get().strip() or None)
            output_path = Path(output_var.get().strip())
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(svg, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - GUI event path
            messagebox.showerror("Render failed", str(exc))
            return

        messagebox.showinfo("Done", f"Overlay written to {output_path}")

    tk.Button(root, text="Render overlay", command=render_selected).pack(pady=(4, 12))
    root.mainloop()
