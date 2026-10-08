# Task Manager

A simple task manager available in two versions: a Python desktop app (Tkinter) and a single-file web app.

## Features

- Add, edit and delete tasks (empty titles are rejected)
- Priority: High, Medium or Low
- Due date in `YYYY-MM-DD` format, validated
- Toggle status between Pending and Completed
- Live search by title
- Filter by All, Pending or Completed
- Sortable table with ID, Title, Priority, Due Date and Status
- Overdue tasks are highlighted in red

## Project Structure

```
.
├── app.py             # Desktop app (Python + Tkinter)
├── tasks.json         # Desktop app data (auto-created if missing)
├── task-manager.html  # Web app (single file, no dependencies)
├── requirements.txt
└── README.md
```

## Desktop App (Python + Tkinter)

### Requirements

- Python 3.10 or newer
- Tkinter (included with Python on Windows and macOS)
  - Debian/Ubuntu: `sudo apt install python3-tk`
  - Fedora: `sudo dnf install python3-tkinter`

No third-party packages are needed.

### Run

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python app.py
```

Use `python3 app.py` if `python` points to Python 2 on your system.

### Usage

| Action | How |
|---|---|
| Add task | **Add Task** button or `Ctrl+N` |
| Edit task | Select a row and click **Edit**, or double-click it |
| Toggle status | Select one or more rows and click **Toggle Status** |
| Delete | Select one or more rows, then click **Delete** or press `Delete` |
| Search | Type in the search box (`Ctrl+F` to focus it) |
| Filter | Use the dropdown, or **Clear** to reset search and filter |
| Sort | Click a column header (click again to reverse) |

### Data Storage

Tasks are saved to `tasks.json` next to `app.py`. The file is created automatically on first launch. Writes are atomic, and if the file is corrupted it is backed up to `tasks.json.bak` before a fresh list is started.

```json
[
  {
    "id": 1,
    "title": "Write report",
    "priority": "High",
    "due_date": "2026-10-15",
    "status": "Pending"
  }
]
```

## Web App

Open `task-manager.html` in any modern browser. There is nothing to install or build.

Tasks are stored in the browser's `localStorage`, so they stay on that device and browser. Clearing site data removes them.

To host it for free, enable GitHub Pages under **Settings > Pages** and select your branch.

## License

MIT. Add a `LICENSE` file if you want to use this license.
