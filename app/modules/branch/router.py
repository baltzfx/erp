from typing import Optional, Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.branch import service, schema
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_branches(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    branches = service.get_branches(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="branch/templates/branch.html",
        context={"branches": branches, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_branch_page(
    request: Request,
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="branch/templates/create-branch.html",
        context={"theme": theme, "user": current_user}
    )

@router.post("/create")
async def create_branch(
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    branch_in = schema.BranchCreate(name=name, description=description)
    service.create_branch(db, branch_in)
    return RedirectResponse(url="/branch/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{branch_id}/edit", response_class=HTMLResponse)
async def edit_branch_page(
    branch_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    branch = service.get_branch(db, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="branch/templates/edit-branch.html",
        context={"branch": branch, "theme": theme, "user": current_user}
    )

@router.post("/{branch_id}/edit")
async def edit_branch(
    branch_id: int,
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    branch_in = schema.BranchUpdate(name=name, description=description)
    service.update_branch(db, branch_id, branch_in)
    return RedirectResponse(url="/branch/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{branch_id}")
async def delete_branch(
    branch_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_branch(db, branch_id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
