from fastapi import APIRouter, Request, Depends, HTTPException, status, Response, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.users import crud, schema as user_schema
from app.modules.users.model import User
from app.modules.auth import service
from app.core.config import settings

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="auth/templates/login.html",
        context={"theme": theme}
    )

@router.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user: User | None = crud.get_user_by_email(db, email=email)
    if not user or not crud.verify_password(password, user.hashed_password):
        # For HTMX, we might want to return a fragment or an error message
        # For now, let's just return a simple error response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    token = service.create_session_token(user.id) # type: ignore

    res = JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/dashboard/"}
    )

    res.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    
    # HTMX redirect to dashboard
    return res

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="auth/templates/register.html",
        context={"theme": theme}
    )

@router.post("/register")
async def register(
    response: Response,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(None),
    last_name: str = Form(None),
    db: Session = Depends(get_db)
):
    if crud.get_user_by_email(db, email=email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_user_by_username(db, username=username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_in = user_schema.UserCreate(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    user = crud.create_user(db, user_in)
    
    token = service.create_session_token(user.id) # type: ignore

    res = JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/dashboard/"}
    )

    res.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    
    return res

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
