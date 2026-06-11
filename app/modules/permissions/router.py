from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi.routing import APIRoute

from app.core.templates import templates
from app.core.database import get_db
from app.modules.permissions import service, schema
from app.api import deps

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    # 1. Fetch existing permissions from the database for correlation
    db_permissions = service.get_permissions(db)
    permission_lookup = {p.codename: p for p in db_permissions}
    seen_codenames = set()

    # 2. Dynamically extract registered routes and "wire" them to database records
    endpoints = []
    for route in request.app.routes:
        # We primarily care about APIRoute instances which represent our functional endpoints
        if isinstance(route, APIRoute):
            # Skip internal FastAPI/OpenAPI utility routes and static assets
            if route.path in ["/openapi.json", "/docs", "/redoc"] or "/static" in route.path:
                continue

            # Use the route name if provided, otherwise the function name
            codename = route.name or route.endpoint.__name__
            seen_codenames.add(codename)
            db_record = permission_lookup.get(codename)

            endpoints.append({
                "name": (db_record.name if db_record and db_record.name else codename.replace("_", " ").replace("-", " ").title()),
                "codename": codename,
                "path": route.path,
                "methods": sorted([m for m in route.methods if m not in ("HEAD", "OPTIONS")]) if hasattr(route, "methods") else [],
                "is_registered": db_record is not None,
                "db_record": db_record,
                "is_orphan": False
            })

    # 3. Add database permissions that don't match any active route (Orphans)
    for codename, perm in permission_lookup.items():
        if codename not in seen_codenames:
            endpoints.append({
                "name": perm.name,
                "codename": perm.codename,
                "path": "N/A (Unmapped)",
                "methods": [],
                "is_registered": True,
                "db_record": perm,
                "is_orphan": True
            })

    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="permissions/templates/permissions.html",
        context={
            "permissions": endpoints,  # Added back for template compatibility
            "endpoints": endpoints,
            "theme": theme,
            "user": current_user
        }
    )

@router.get("/create", response_class=HTMLResponse)
async def create_permission_page(
    request: Request,
    current_user = Depends(deps.get_current_user)
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="permissions/templates/create-permission.html",
        context={"theme": theme, "user": current_user}
    )

@router.post("/create")
async def create_permission(
    name: str = Form(...),
    codename: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    permission_in = schema.PermissionCreate(name=name, codename=codename, description=description)
    service.create_permission(db, permission_in)
    return RedirectResponse(url="/permissions/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{permission_id}/edit", response_class=HTMLResponse)
async def edit_permission_page(
    permission_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    permission = service.get_permission(db, permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="permissions/templates/edit-permission.html",
        context={"permission": permission, "theme": theme, "user": current_user}
    )

@router.post("/{permission_id}/edit")
async def edit_permission(
    permission_id: int,
    name: str = Form(...),
    codename: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    permission_in = schema.PermissionUpdate(name=name, codename=codename, description=description)
    service.update_permission(db, permission_id, permission_in)
    return RedirectResponse(url="/permissions/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user)
):
    service.delete_permission(db, permission_id)
    return RedirectResponse(url="/permissions/", status_code=status.HTTP_303_SEE_OTHER)
