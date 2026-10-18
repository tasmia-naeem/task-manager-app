from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="TaskFlow")

# Files under /static/... (style.css, theme.js) are served from this folder.
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Tell Jinja2 which folder contains the HTML templates.
templates = Jinja2Templates(directory=BASE_DIR / "templates")
PRIORITIES = ("Low", "Medium", "High")
DEFAULT_PRIORITY = "Medium"
STATUS_FILTERS = ("All", "Pending", "Completed")

# Page heading for every view of the home route.
PAGE_TITLES = {
    "": "Dashboard",
    "All": "All Tasks",
    "Pending": "Pending",
    "Completed": "Completed",
}

# Validation limits
TITLE_MAX = 80
DESC_MAX = 300
QUERY_MAX = 100
CURRENT_USER = {"name": "Guest User", "plan": "Free plan"}
FLASH_MESSAGES = {
    "created": "Task created successfully.",
    "updated": "Task updated.",
    "completed": "Task marked as Completed. Nice work!",
    "reopened": "Task moved back to Pending.",
    "deleted": "Task deleted.",
}
_today = date.today()

tasks = [
    {
        "id": 1,
        "title": "Design the TaskFlow dashboard",
        "description": "Final polish for the sidebar, stat cards and dark/light theme.",
        "status": "Completed",
        "priority": "High",
        "due_date": (_today - timedelta(days=1)).isoformat(),
    },
    {
        "id": 2,
        "title": "Prepare for technical review",
        "description": "Practice explaining list vs dict, GET vs POST and ID lookup in my own words.",
        "status": "Pending",
        "priority": "High",
        "due_date": (_today + timedelta(days=2)).isoformat(),
    },
    {
        "id": 3,
        "title": "Write README and take screenshots",
        "description": "Add setup steps, features and desktop + mobile screenshots.",
        "status": "Pending",
        "priority": "Medium",
        "due_date": (_today + timedelta(days=5)).isoformat(),
    },
    {
        "id": 4,
        "title": "Reply to code review comments",
        "description": "Go through the feedback and push the requested fixes.",
        "status": "Pending",
        "priority": "Medium",
        "due_date": (_today - timedelta(days=1)).isoformat(),
    },
    {
        "id": 5,
        "title": "Plan next week's goals",
        "description": "",
        "status": "Pending",
        "priority": "Low",
        "due_date": "",
    },
]

# FIX: ye line missing thi is liye Internal Server Error aa raha tha
next_id = 6

def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None

def validate_task(title: str, description: str, priority: str, due_date: str):
    errors = {}
    if not title:
        errors["title"] = "Title cannot be empty. Please enter a title."
    elif len(title) > TITLE_MAX:
        errors["title"] = f"Title cannot be longer than {TITLE_MAX} characters."
    if len(description) > DESC_MAX:
        errors["description"] = f"Description cannot be longer than {DESC_MAX} characters."
    if priority not in PRIORITIES:
        errors["priority"] = "Please choose Low, Medium or High."
    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError:
            errors["due_date"] = "Please pick a valid due date."
    return errors

def normalize_due_date(due_date: str) -> str:
    return date.fromisoformat(due_date).isoformat() if due_date else ""

def format_date(value: date) -> str:
    return f"{value.strftime('%b')} {value.day}, {value.year}"

def decorate_task(task: dict) -> dict:
    item = dict(task)
    item.update({"due_label": "", "due_note": "", "due_state": ""})
    if task["due_date"]:
        due = date.fromisoformat(task["due_date"])
        item["due_label"] = format_date(due)
        if task["status"] != "Completed":
            days_left = (due - date.today()).days
            if days_left < 0:
                item["due_note"], item["due_state"] = "Overdue", "overdue"
            elif days_left == 0:
                item["due_note"], item["due_state"] = "Due today", "today"
            elif days_left == 1:
                item["due_note"], item["due_state"] = "Due tomorrow", "soon"
    return item

def matches_query(task: dict, query: str) -> bool:
    needle = query.lower()
    return needle in task["title"].lower() or needle in task["description"].lower()

def get_stats():
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Completed")
    high = [t for t in tasks if t["priority"] == "High"]
    return {
        "total": total,
        "pending": total - completed,
        "completed": completed,
        "percent": round(completed / total * 100) if total else 0,
        "high": len(high),
        "high_open": sum(1 for t in high if t["status"] != "Completed"),
    }

def layout_context(view, q: str):
    initials = "".join(word[0] for word in CURRENT_USER["name"].split()[:2]).upper()
    return {
        "view": view,
        "q": q,
        "q_param": f"&q={quote(q)}" if q else "",
        "view_url": f"/?status={view}" if view in STATUS_FILTERS else "/",
        "stats": get_stats(),
        "user": {**CURRENT_USER, "initials": initials},
    }

def redirect_home(status: str = "", msg: str = "", q: str = ""):
    params = []
    if status in STATUS_FILTERS:
        params.append(f"status={quote(status)}")
    if q:
        params.append(f"q={quote(q)}")
    if msg:
        params.append(f"msg={quote(msg)}")
    url = "/" + ("?" + "&".join(params) if params else "")
    return RedirectResponse(url, status_code=303)

def render_home(request: Request, status: str = "", q: str = "", msg: str = "",
                errors=None, form=None, http_status: int = 200):
    if status not in STATUS_FILTERS:
        status = ""
    q = q.strip()[:QUERY_MAX]
    visible = [t for t in tasks if status in ("", "All") or t["status"] == status]
    if q:
        visible = [t for t in visible if matches_query(t, q)]
    context = {
        **layout_context(status, q),
        "page_title": PAGE_TITLES[status],
        "tasks": [decorate_task(t) for t in visible],
        "result_count": len(visible),
        "filters": STATUS_FILTERS,
        "priorities": PRIORITIES,
        "flash": FLASH_MESSAGES.get(msg),
        "errors": errors or {},
        "form": form or {"title": "", "description": "", "priority": DEFAULT_PRIORITY, "due_date": ""},
        "composer_open": bool(errors),
        "title_max": TITLE_MAX,
        "desc_max": DESC_MAX,
    }
    return templates.TemplateResponse(request, "index.html", context, status_code=http_status)

def render_edit(request: Request, task: dict, errors=None, form=None, http_status: int = 200):
    context = {
        **layout_context(None, ""),
        "page_title": "Edit task",
        "task": task,
        "errors": errors or {},
        "form": form or task,
        "priorities": PRIORITIES,
        "title_max": TITLE_MAX,
        "desc_max": DESC_MAX,
    }
    return templates.TemplateResponse(request, "edit.html", context, status_code=http_status)

@app.get("/", response_class=HTMLResponse)
def home(request: Request, status: str = "", q: str = "", msg: str = ""):
    return render_home(request, status=status, q=q, msg=msg)

@app.post("/add-task")
def add_task(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    priority: str = Form(DEFAULT_PRIORITY),
    due_date: str = Form(""),
    status: str = Form(""),
    q: str = Form(""),
):
    global next_id
    title = title.strip()
    description = description.strip()
    due_date = due_date.strip()
    errors = validate_task(title, description, priority, due_date)
    if errors:
        return render_home(
            request,
            status=status,
            q=q,
            errors=errors,
            form={"title": title, "description": description, "priority": priority, "due_date": due_date},
            http_status=400,
        )
    tasks.append(
        {
            "id": next_id,
            "title": title,
            "description": description,
            "status": "Pending",
            "priority": priority,
            "due_date": normalize_due_date(due_date),
        }
    )
    next_id += 1
    return redirect_home(status, "created", q)

@app.post("/complete/{task_id}")
def toggle_complete(task_id: int, status: str = Form(""), q: str = Form("")):
    task = find_task(task_id)
    if task is None:
        return redirect_home(status, "", q)
    if task["status"] == "Pending":
        task["status"] = "Completed"
        return redirect_home(status, "completed", q)
    task["status"] = "Pending"
    return redirect_home(status, "reopened", q)

@app.post("/delete/{task_id}")
def delete_task(task_id: int, status: str = Form(""), q: str = Form("")):
    task = find_task(task_id)
    if task is not None:
        tasks.remove(task)
    return redirect_home(status, "deleted" if task else "", q)

@app.get("/edit/{task_id}", response_class=HTMLResponse)
def edit_page(request: Request, task_id: int):
    task = find_task(task_id)
    if task is None:
        return RedirectResponse("/", status_code=303)
    return render_edit(request, task)

@app.post("/edit/{task_id}")
def edit_task(
    request: Request,
    task_id: int,
    title: str = Form(""),
    description: str = Form(""),
    priority: str = Form(DEFAULT_PRIORITY),
    due_date: str = Form(""),
    task_status: str = Form("Pending"),
):
    task = find_task(task_id)
    if task is None:
        return RedirectResponse("/", status_code=303)
    title = title.strip()
    description = description.strip()
    due_date = due_date.strip()
    errors = validate_task(title, description, priority, due_date)
    if errors:
        return render_edit(
            request,
            task,
            errors=errors,
            form={"title": title, "description": description, "priority": priority,
                  "due_date": due_date, "status": task_status},
            http_status=400,
        )
    task["title"] = title
    task["description"] = description
    task["priority"] = priority
    task["due_date"] = normalize_due_date(due_date)
    if task_status in ("Pending", "Completed"):
        task["status"] = task_status
    return redirect_home("", "updated")