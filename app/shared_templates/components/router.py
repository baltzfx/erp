from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import date

from app.core.templates import templates
from app.core.database import get_db
from app.modules.holiday import service, schema, model
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_holidays(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    holidays = service.get_holidays(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="holiday/templates/holidays.html",
        context={"holidays": holidays, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_holiday_page(
    request: Request,
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="holiday/templates/create-holiday.html",
        context={
            "theme": theme, 
            "user": current_user,
            "holiday_types": model.HolidayType
        }
    )

@router.post("/create")
async def create_holiday(
    name: Annotated[str, Form(...)],
    holiday_date: Annotated[date, Form(alias="date")],
    holiday_type: Annotated[model.HolidayType, Form(...)],
    description: Annotated[Optional[str], Form()] = None,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    holiday_in = schema.HolidayCreate(
        name=name,
        date=holiday_date,
        holiday_type=holiday_type,
        description=description
    )
    service.create_holiday(db, holiday_in)
    return RedirectResponse(url="/holiday/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{holiday_id}/edit", response_class=HTMLResponse)
async def edit_holiday_page(
    holiday_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    holiday = service.get_holiday(db, holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="holiday/templates/edit-holiday.html",
        context={
            "holiday": holiday, 
            "theme": theme, 
            "user": current_user,
            "holiday_types": model.HolidayType
        }
    )