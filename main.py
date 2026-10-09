from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------------------------
# 1. APP SETUP
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="TaskFlow")

# Files under /static/... (style.css, theme.js) are served from this folder.
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Tell Jinja2 which folder contains the HTML templates.
templates = Jinja2Templates(directory=BASE_DIR / "templates")

tasks = [
    {
        "id": 1,
        "title": "Complete task filtering logic",
        "description": "Implement All, Pending and Completed filters and highlight active tab.",
        "status": "Completed",
    },
    {
        "id": 2,
        "title": "Add form validation",
        "description": "Validate title and description length and show error messages on the form.",
        "status": "Pending",
    },
    {
        "id": 3,
        "title": "Test delete and complete features",
        "description": "Check delete and mark as complete functionality for all tasks.",
        "status": "Pending",
    },
]
next_id = 4

# Validation limits
TITLE_MAX = 80
DESC_MAX = 300

VALID_FILTERS = ("All", "Pending", "Completed")
FLASH_MESSAGES = {
    "created": "Task created successfully.",
    "updated": "Task updated.",
    "completed": "Task marked as Completed. Nice work!",
    "reopened": "Task moved back to Pending.",
    "deleted": "Task deleted.",
}
# ---------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def find_task(task_id: int):

    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def validate(title: str, description: str):
    errors = {}
    if not title:
        errors["title"] = "Title cannot be empty. Please enter a title."
    elif len(title) > TITLE_MAX:
        errors["title"] = f"Title cannot be longer than {TITLE_MAX} characters."
    if len(description) > DESC_MAX:
        errors["description"] = f"Description cannot be longer than {DESC_MAX} characters."
    return errors


def get_stats():
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Completed")
    pending = total - completed
    percent = round(completed / total * 100) if total else 0
    return {"total": total, "pending": pending, "completed": completed, "percent": percent}


def redirect_home(status: str, msg: str):
    
    if status not in VALID_FILTERS:
        status = "All"
    return RedirectResponse(f"/?status={quote(status)}&msg={quote(msg)}", status_code=303)


def render_home(request: Request, status: str = "All", msg: str = "",
                errors=None, form=None, http_status: int = 200):

    if status not in VALID_FILTERS:
        status = "All"

    # Filter: keep only the tasks whose status matches.
    if status == "All":
        visible_tasks = tasks
    else:
        visible_tasks = [t for t in tasks if t["status"] == status]

    context = {
        "tasks": visible_tasks,            # available as {{ tasks }} in the template
        "current_filter": status,          # used to highlight the active filter tab
        "filters": VALID_FILTERS,
        "stats": get_stats(),
        "flash": FLASH_MESSAGES.get(msg),  # unknown key -> None -> nothing is shown
        "errors": errors or {},
        "form": form or {"title": "", "description": ""},
        "title_max": TITLE_MAX,
        "desc_max": DESC_MAX,
    }
    return templates.TemplateResponse(request, "index.html", context, status_code=http_status)



@app.get("/", response_class=HTMLResponse)
def home(request: Request, status: str = "All", msg: str = ""):
    """Home page, filtered by the query param (/?status=All|Pending|Completed)."""
    return render_home(request, status=status, msg=msg)


@app.post("/add-task")
def add_task(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    status: str = Form("All"),
):
    """Creates a new task. Form fields are read with Form(...)."""
    global next_id  # next_id is a module-level variable, so we must declare it global

    title = title.strip()
    description = description.strip()

    errors = validate(title, description)
    if errors:
        # Invalid input: show the page again with error messages and the user's text.
        return render_home(
            request,
            status=status,
            errors=errors,
            form={"title": title, "description": description},
            http_status=400,
        )

    tasks.append(
        {
            "id": next_id,            # auto-generated unique ID
            "title": title,
            "description": description,
            "status": "Pending",      # default status
        }
    )
    next_id += 1
    return redirect_home(status, "created")


@app.post("/complete/{task_id}")
def toggle_complete(task_id: int, status: str = Form("All")):
    """Toggles status: Pending <-> Completed. task_id comes from the URL path."""
    task = find_task(task_id)
    if task is None:
        return redirect_home(status, "")  # task was already deleted - just go back
    if task["status"] == "Pending":
        task["status"] = "Completed"
        return redirect_home(status, "completed")
    task["status"] = "Pending"
    return redirect_home(status, "reopened")


@app.post("/delete/{task_id}")
def delete_task(task_id: int, status: str = Form("All")):
    """Removes the task from the list."""
    task = find_task(task_id)
    if task is not None:
        tasks.remove(task)  # removes that exact dict from the list
    return redirect_home(status, "deleted" if task else "")


@app.get("/edit/{task_id}", response_class=HTMLResponse)
def edit_page(request: Request, task_id: int):
    """Shows the edit form with the old values already filled in."""
    task = find_task(task_id)
    if task is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request,
        "edit.html",
        {"task": task, "errors": {}, "form": task, "title_max": TITLE_MAX, "desc_max": DESC_MAX},
    )


@app.post("/edit/{task_id}")
def edit_task(
    request: Request,
    task_id: int,
    title: str = Form(""),
    description: str = Form(""),
    task_status: str = Form("Pending"),
):
    """Edit form submit: validates, then updates the task."""
    task = find_task(task_id)
    if task is None:
        return RedirectResponse("/", status_code=303)

    title = title.strip()
    description = description.strip()
    errors = validate(title, description)
    if errors:
        return templates.TemplateResponse(
            request,
            "edit.html",
            {
                "task": task,
                "errors": errors,
                "form": {"title": title, "description": description, "status": task_status},
                "title_max": TITLE_MAX,
                "desc_max": DESC_MAX,
            },
            status_code=400,
        )

    task["title"] = title
    task["description"] = description
    if task_status in ("Pending", "Completed"):
        task["status"] = task_status
    return redirect_home("All", "updated")



