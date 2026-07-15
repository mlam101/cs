from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

from .demoparser_extractor import Demoparser2Extractor
from .models import PathTrace
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

    demo_files: list[Path] = []

    def refresh_demo_list() -> None:
        nonlocal demo_files
        demo_files = sorted(demos_dir.glob("*.dem"))
        listbox.delete(0, tk.END)
        if not demo_files:
            listbox.insert(tk.END, "No .dem files found in demos folder.")
            listbox.configure(state=tk.DISABLED)
            return
        listbox.configure(state=tk.NORMAL)
        for demo_file in demo_files:
            listbox.insert(tk.END, demo_file.name)

    refresh_demo_list()

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

    def upload_demos() -> None:
        selected_files = filedialog.askopenfilenames(
            title="Upload CS demos",
            filetypes=[("CS demo files", "*.dem"), ("All files", "*.*")],
        )
        if not selected_files:
            return

        copied = 0
        for source in selected_files:
            src_path = Path(source)
            if src_path.suffix.lower() != ".dem":
                continue
            destination = demos_dir / src_path.name
            if destination.exists():
                stem = src_path.stem
                suffix = src_path.suffix
                counter = 1
                while destination.exists():
                    destination = demos_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            shutil.copy2(src_path, destination)
            copied += 1

        refresh_demo_list()
        if copied:
            messagebox.showinfo("Upload complete", f"Uploaded {copied} demo file(s).")
        else:
            messagebox.showerror("Upload failed", "No valid .dem files were selected.")

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
            _open_playback_window(root, paths=paths, title=title_var.get().strip() or "CS Demo Playback")
            svg = render_overlay_svg(paths=paths, title=title_var.get().strip() or None)
            output_path = Path(output_var.get().strip())
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(svg, encoding="utf-8")
        except Exception as exc:  # pragma: no cover - GUI event path
            error_message = str(exc)
            if "entity" in error_message.lower() and "not found" in error_message.lower():
                error_message = (
                    "Demo parse failed due to missing entities. "
                    "Try a different demo version or update demoparser2."
                )
            messagebox.showerror("Render failed", error_message)
            return

        messagebox.showinfo("Done", f"Playback opened and overlay written to {output_path}")

    actions = tk.Frame(root)
    actions.pack(pady=(4, 12))
    tk.Button(actions, text="Upload demos", command=upload_demos).pack(side=tk.LEFT, padx=4)
    tk.Button(actions, text="Render overlay", command=render_selected).pack(side=tk.LEFT, padx=4)
    root.mainloop()


def _open_playback_window(root: tk.Tk, paths: list[PathTrace], title: str) -> None:
    if not paths:
        raise ValueError("No paths found for selected demos")

    playback = tk.Toplevel(root)
    playback.title(title)
    canvas_width = 980
    canvas_height = 780
    padding = 24
    playback.geometry(f"{canvas_width}x{canvas_height + 110}")

    canvas = tk.Canvas(playback, width=canvas_width, height=canvas_height, bg="#0f172a", highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=10, pady=10)

    all_points = [point for path in paths for point in path.points]
    min_x = min(point.x for point in all_points)
    max_x = max(point.x for point in all_points)
    min_y = min(point.y for point in all_points)
    max_y = max(point.y for point in all_points)

    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    scale_x = (canvas_width - 2 * padding) / span_x
    scale_y = (canvas_height - 2 * padding) / span_y

    max_steps = max(len(path.points) for path in paths)
    current_step = tk.IntVar(value=1)
    playing = {"active": False}

    def scale_point(x: float, y: float) -> tuple[float, float]:
        return (
            padding + (x - min_x) * scale_x,
            canvas_height - padding - (y - min_y) * scale_y,
        )

    def draw_frame(step: int) -> None:
        canvas.delete("all")
        for path in paths:
            color = _color_for_label(path.match_label)
            frame_points = path.points[: max(1, min(step, len(path.points)))]
            if len(frame_points) >= 2:
                scaled = [scale_point(point.x, point.y) for point in frame_points]
                flat_points = [coord for point in scaled for coord in point]
                canvas.create_line(*flat_points, fill=color, width=2, smooth=True)
            marker_point = frame_points[-1]
            marker_x, marker_y = scale_point(marker_point.x, marker_point.y)
            canvas.create_oval(marker_x - 4, marker_y - 4, marker_x + 4, marker_y + 4, fill=color, outline="")
        canvas.create_text(
            10,
            10,
            anchor="nw",
            text=f"Step {step}/{max_steps}",
            fill="#e2e8f0",
            font=("Arial", 12, "bold"),
        )

    def on_slider_move(value: str) -> None:
        current = max(1, min(int(float(value)), max_steps))
        current_step.set(current)
        draw_frame(current)

    def playback_tick() -> None:
        if not playing["active"] or not playback.winfo_exists():
            return
        next_step = current_step.get() + 1
        if next_step > max_steps:
            playing["active"] = False
            play_button.configure(text="Play")
            return
        slider.set(next_step)
        draw_frame(next_step)
        playback.after(50, playback_tick)

    def toggle_play() -> None:
        playing["active"] = not playing["active"]
        play_button.configure(text="Pause" if playing["active"] else "Play")
        if playing["active"]:
            playback_tick()

    controls = tk.Frame(playback)
    controls.pack(fill="x", padx=10, pady=(0, 10))
    slider = tk.Scale(
        controls,
        from_=1,
        to=max_steps,
        orient=tk.HORIZONTAL,
        showvalue=False,
        variable=current_step,
        command=on_slider_move,
    )
    slider.pack(side=tk.LEFT, fill="x", expand=True)
    play_button = tk.Button(controls, text="Play", command=toggle_play)
    play_button.pack(side=tk.LEFT, padx=(8, 0))

    draw_frame(current_step.get())


def _color_for_label(label: str) -> str:
    digest = sha256(label.encode("utf-8")).hexdigest()
    return f"#{digest[:6]}"
