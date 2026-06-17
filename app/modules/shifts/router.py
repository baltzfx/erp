from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import time

from app.core.templates import templates
from app.core.database import get_db
from app.modules.shifts import service, schema
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_shifts(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    shifts = service.get_shifts(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="shifts/templates/shifts/shifts.html",
        context={"shifts": shifts, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_shift_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="shifts/templates/shifts/create-shift.html",
        context={"theme": theme, "user": current_user}
    )

@router.post("/create")
async def create_shift(
    name: Annotated[str, Form(...)],
    start_time: Annotated[time, Form(...)],
    end_time: Annotated[time, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    shift_in = schema.ShiftCreate(
        name=name,
        start_time=start_time,
        end_time=end_time,
        description=description
    )
    service.create_shift(db, shift_in)
    return RedirectResponse(url="/shifts/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{shift_id}/edit", response_class=HTMLResponse)
async def edit_shift_page(
    shift_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    shift = service.get_shift(db, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="shifts/templates/shifts/edit-shift.html",
        context={"shift": shift, "theme": theme, "user": current_user}
    )

@router.post("/{shift_id}/edit")
async def edit_shift(
    shift_id: int,
    name: Annotated[str, Form(...)],
    start_time: Annotated[time, Form(...)],
    end_time: Annotated[time, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    shift_in = schema.ShiftUpdate(
        name=name,
        start_time=start_time,
        end_time=end_time,
        description=description
    )
    service.update_shift(db, shift_id, shift_in)
    return RedirectResponse(url="/shifts/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_shift(db, shift_id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
