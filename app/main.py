from datetime import datetime

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import Base, Submission
from starlette.status import HTTP_302_FOUND
from passlib.hash import bcrypt
from starlette.middleware.sessions import SessionMiddleware

DATABASE_URL = "postgresql://postgres:password@dbassets:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key='your_secret_key')
templates = Jinja2Templates(directory="app/templates")

# Загрузка статики
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    current_year = datetime.now().year
    return templates.TemplateResponse("index.html", {"request": request, "current_year": current_year})
async def not_found(request: Request, exc: HTTPException):
    current_year = datetime.now().year
    return templates.TemplateResponse("404.html", {"request": request, "current_year": current_year})
app.add_exception_handler(404, not_found)
@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    course: int = Form(...),
    direction: str = Form(...),
    telegram: str = Form(...),
):
    db = SessionLocal()
    submission = Submission(
        first_name=first_name,
        last_name=last_name,
        course=course,
        direction=direction,
        telegram=telegram,
    )
    db.add(submission)
    db.commit()
    db.close()
    current_year = datetime.now().year
    # Передаем message в шаблон для отображения сообщения об успешной отправке
    return templates.TemplateResponse("index.html", {"request": request, "message": "success", "current_year": current_year})
@app.get("/admin", response_class=HTMLResponse)
async def admin_login(request: Request):
    if request.session.get("logged_in"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/admin", response_class=HTMLResponse)
async def admin_auth(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == "iloveegor" and password == "ilovekmk":
        request.session["logged_in"] = True
        return RedirectResponse(url="/dashboard", status_code=HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверные данные для входа"})

@app.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/admin")
    db = SessionLocal()
    submissions = db.query(Submission).all()
    db.close()
    return templates.TemplateResponse("admin.html", {"request": request, "submissions": submissions})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

@app.get("/export")
async def export_csv(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/admin")
    db = SessionLocal()
    submissions = db.query(Submission).all()
    db.close()

    import csv
    from io import StringIO
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(['ID', 'Имя', 'Фамилия', 'Курс', 'Направление', 'Telegram'])
    for s in submissions:
        writer.writerow([s.id, s.first_name, s.last_name, s.course, s.direction, s.telegram])

    response = HTMLResponse(content=csv_file.getvalue(), media_type='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=submissions.csv"
    return response
