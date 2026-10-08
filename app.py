#!/usr/bin/env python3
"""Task Manager - a Tkinter desktop app with JSON persistence."""

import json
import os
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "tasks.json")

PRIORITIES = ("High", "Medium", "Low")
STATUSES = ("Pending", "Completed")
FILTERS = ("All",) + STATUSES
PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}
DATE_FORMAT = "%Y-%m-%d"


def is_valid_date(text: str) -> bool:
    """Strictly validate YYYY-MM-DD."""
    try:
        return datetime.strptime(text, DATE_FORMAT).strftime(DATE_FORMAT) == text
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------
# Data layer
# --------------------------------------------------------------------------
class TaskStore:
    """Loads, holds and persists tasks in a JSON file."""

    def __init__(self, path: str = DATA_FILE):
        self.path = path
        self.tasks: list[dict] = []
        self.load_warning: str | None = None
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            self._save()  # auto-create an empty tasks.json
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Root element must be a list.")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            backup = self.path + ".bak"
            try:
                os.replace(self.path, backup)
                self.load_warning = (
                    f"tasks.json could not be read ({exc}).\n"
                    f"The old file was saved as:\n{backup}\n\nStarting with an empty list."
                )
            except OSError:
                self.load_warning = f"tasks.json could not be read ({exc})."
            self.tasks = []
            self._save()
            return

        for item in data:
            if not isinstance(item, dict) or not str(item.get("title", "")).strip():
                continue
            try:
                task_id = int(item.get("id", 0))
            except (TypeError, ValueError):
                task_id = 0
            if task_id <= 0 or any(t["id"] == task_id for t in self.tasks):
                task_id = self._next_id()
            self.tasks.append(
                {
                    "id": task_id,
                    "title": str(item["title"]).strip(),
                    "priority": item.get("priority") if item.get("priority") in PRIORITIES else "Medium",
                    "due_date": item.get("due_date", "") if is_valid_date(item.get("due_date", "")) else "",
                    "status": item.get("status") if item.get("status") in STATUSES else "Pending",
                }
            )

    def _save(self) -> None:
        """Atomic write so a crash can't corrupt the file."""
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError as exc:
            raise RuntimeError(f"Could not save tasks: {exc}") from exc

    def _next_id(self) -> int:
        return max((t["id"] for t in self.tasks), default=0) + 1

    def add(self, title, priority, due_date, status="Pending") -> dict:
        task = {
            "id": self._next_id(),
            "title": title,
            "priority": priority,
            "due_date": due_date,
            "status": status,
        }
        self.tasks.append(task)
        self._save()
        return task

    def get(self, task_id: int) -> dict | None:
        return next((t for t in self.tasks if t["id"] == task_id), None)

    def update(self, task_id, title, priority, due_date, status) -> None:
        task = self.get(task_id)
        if task:
            task.update(title=title, priority=priority, due_date=due_date, status=status)
            self._save()

    def delete(self, task_ids) -> None:
        ids = set(task_ids)
        self.tasks = [t for t in self.tasks if t["id"] not in ids]
        self._save()

    def toggle(self, task_ids) -> None:
        ids = set(task_ids)
        for t in self.tasks:
            if t["id"] in ids:
                t["status"] = "Completed" if t["status"] == "Pending" else "Pending"
        self._save()


# --------------------------------------------------------------------------
# Add / Edit dialog
# --------------------------------------------------------------------------
class TaskDialog(tk.Toplevel):
    def __init__(self, parent, heading: str, task: dict | None = None):
        super().__init__(parent)
        self.title(heading)
        self.resizable(False, False)
        self.transient(parent)
        self.result: dict | None = None

        task = task or {}
        self.title_var = tk.StringVar(value=task.get("title", ""))
        self.priority_var = tk.StringVar(value=task.get("priority", "Medium"))
        self.due_var = tk.StringVar(value=task.get("due_date", ""))
        self.status_var = tk.StringVar(value=task.get("status", "Pending"))

        frm = ttk.Frame(self, padding=15)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="Title *").grid(row=0, column=0, sticky="w", pady=4)
        title_entry = ttk.Entry(frm, textvariable=self.title_var, width=36)
        title_entry.grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Priority").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(frm, textvariable=self.priority_var, values=PRIORITIES,
                     state="readonly", width=15).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="Due date").grid(row=2, column=0, sticky="w", pady=4)
        due_box = ttk.Frame(frm)
        due_box.grid(row=2, column=1, sticky="w", pady=4)
        ttk.Entry(due_box, textvariable=self.due_var, width=15).pack(side="left")
        ttk.Label(due_box, text="  YYYY-MM-DD (optional)", foreground="gray").pack(side="left")
        ttk.Button(due_box, text="Today", width=6,
                   command=lambda: self.due_var.set(date.today().strftime(DATE_FORMAT))
                   ).pack(side="left", padx=(8, 0))

        ttk.Label(frm, text="Status").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Combobox(frm, textvariable=self.status_var, values=STATUSES,
                     state="readonly", width=15).grid(row=3, column=1, sticky="w", pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Save", command=self._on_save).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left")

        self.bind("<Return>", lambda e: self._on_save())
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        title_entry.focus_set()
        self.grab_set()
        self.wait_window(self)

    def _on_save(self) -> None:
        title = self.title_var.get().strip()
        due = self.due_var.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title cannot be empty.", parent=self)
            return
        if due and not is_valid_date(due):
            messagebox.showwarning(
                "Validation", "Due date must be in YYYY-MM-DD format (e.g. 2026-12-31).", parent=self
            )
            return
        self.result = {
            "title": title,
            "priority": self.priority_var.get(),
            "due_date": due,
            "status": self.status_var.get(),
        }
        self.destroy()


# --------------------------------------------------------------------------
# Main application
# --------------------------------------------------------------------------
class TaskManagerApp(tk.Tk):
    COLUMNS = (
        ("id", "ID", 60, "center"),
        ("title", "Title", 340, "w"),
        ("priority", "Priority", 90, "center"),
        ("due_date", "Due Date", 110, "center"),
        ("status", "Status", 100, "center"),
    )

    def __init__(self):
        super().__init__()
        self.title("Task Manager")
        self.geometry("780x500")
        self.minsize(640, 380)

        self.store = TaskStore()
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")
        self.status_text = tk.StringVar()
        self.sort_col = "id"
        self.sort_desc = False

        self._build_ui()
        self._bind_events()
        self.refresh()

        if self.store.load_warning:
            messagebox.showwarning("Data file problem", self.store.load_warning)

    # ---- UI construction -------------------------------------------------
    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=(10, 10, 10, 4))
        top.pack(fill="x")
        ttk.Label(top, text="Search:").pack(side="left")
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=28)
        self.search_entry.pack(side="left", padx=(4, 12))
        ttk.Label(top, text="Filter:").pack(side="left")
        ttk.Combobox(top, textvariable=self.filter_var, values=FILTERS,
                     state="readonly", width=11).pack(side="left", padx=4)
        ttk.Button(top, text="Clear", command=self._clear_filters).pack(side="left", padx=8)

        bar = ttk.Frame(self, padding=(10, 4))
        bar.pack(fill="x")
        for text, cmd in (
            ("Add Task", self.add_task),
            ("Edit", self.edit_task),
            ("Toggle Status", self.toggle_status),
            ("Delete", self.delete_tasks),
        ):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(0, 6))

        # Status bar must be packed before the expanding table so it stays visible.
        ttk.Label(self, textvariable=self.status_text, anchor="w", relief="sunken",
                  padding=(8, 2)).pack(fill="x", side="bottom")

        wrap = ttk.Frame(self, padding=(10, 4))
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(
            wrap, columns=[c[0] for c in self.COLUMNS], show="headings", selectmode="extended"
        )
        for key, label, width, anchor in self.COLUMNS:
            self.tree.heading(key, text=label, command=lambda k=key: self._sort_by(k))
            self.tree.column(key, width=width, anchor=anchor, stretch=(key == "title"))
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.tag_configure("overdue", foreground="#c0392b")
        self.tree.tag_configure("done", foreground="#7f8c8d")

    def _bind_events(self) -> None:
        self.search_var.trace_add("write", lambda *_: self.refresh())
        self.filter_var.trace_add("write", lambda *_: self.refresh())
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Delete>", lambda e: self.delete_tasks())
        self.bind("<Control-n>", lambda e: self.add_task())
        self.bind("<Control-f>", lambda e: self.search_entry.focus_set())

    def _on_double_click(self, event) -> None:
        if self.tree.identify_region(event.x, event.y) == "cell":
            self.edit_task()

    # ---- Table helpers ---------------------------------------------------
    def _sort_key(self, task: dict):
        if self.sort_col == "priority":
            return PRIORITY_RANK[task["priority"]]
        if self.sort_col == "id":
            return task["id"]
        if self.sort_col == "due_date":
            return (task["due_date"] == "", task["due_date"])  # blanks last
        return str(task[self.sort_col]).lower()

    def _sort_by(self, col: str) -> None:
        self.sort_desc = (not self.sort_desc) if col == self.sort_col else False
        self.sort_col = col
        self.refresh()

    def _clear_filters(self) -> None:
        self.search_var.set("")
        self.filter_var.set("All")

    def refresh(self) -> None:
        selected = set(self.tree.selection())
        query = self.search_var.get().strip().lower()
        flt = self.filter_var.get()
        today = date.today().strftime(DATE_FORMAT)

        visible = [
            t for t in self.store.tasks
            if (flt == "All" or t["status"] == flt) and query in t["title"].lower()
        ]
        visible.sort(key=self._sort_key, reverse=self.sort_desc)

        self.tree.delete(*self.tree.get_children())
        for t in visible:
            tags = ()
            if t["status"] == "Completed":
                tags = ("done",)
            elif t["due_date"] and t["due_date"] < today:
                tags = ("overdue",)
            self.tree.insert(
                "", "end", iid=str(t["id"]), tags=tags,
                values=(t["id"], t["title"], t["priority"], t["due_date"] or "-", t["status"]),
            )
        keep = [i for i in selected if self.tree.exists(i)]
        if keep:
            self.tree.selection_set(keep)

        pending = sum(1 for t in self.store.tasks if t["status"] == "Pending")
        self.status_text.set(
            f"Showing {len(visible)} of {len(self.store.tasks)} tasks  |  {pending} pending"
            "  |  Red = overdue"
        )

    def _selected_ids(self) -> list[int]:
        return [int(i) for i in self.tree.selection()]

    # ---- Actions ---------------------------------------------------------
    def _safe(self, action) -> None:
        try:
            action()
        except RuntimeError as exc:
            messagebox.showerror("Save error", str(exc), parent=self)
        self.refresh()

    def add_task(self) -> None:
        dlg = TaskDialog(self, "Add Task")
        if dlg.result:
            r = dlg.result
            self._safe(lambda: self.store.add(r["title"], r["priority"], r["due_date"], r["status"]))

    def edit_task(self) -> None:
        ids = self._selected_ids()
        if len(ids) != 1:
            messagebox.showinfo("Edit Task", "Select exactly one task to edit.", parent=self)
            return
        task = self.store.get(ids[0])
        if not task:
            return
        dlg = TaskDialog(self, "Edit Task", task)
        if dlg.result:
            r = dlg.result
            self._safe(lambda: self.store.update(
                task["id"], r["title"], r["priority"], r["due_date"], r["status"]))

    def toggle_status(self) -> None:
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Toggle Status", "Select at least one task.", parent=self)
            return
        self._safe(lambda: self.store.toggle(ids))

    def delete_tasks(self) -> None:
        ids = self._selected_ids()
        if not ids:
            messagebox.showinfo("Delete", "Select at least one task to delete.", parent=self)
            return
        noun = "task" if len(ids) == 1 else f"{len(ids)} tasks"
        if messagebox.askyesno("Confirm delete", f"Delete the selected {noun}?", parent=self):
            self._safe(lambda: self.store.delete(ids))


def main() -> None:
    TaskManagerApp().mainloop()


if __name__ == "__main__":
    main()
