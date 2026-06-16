from typing import Annotated, Optional, Any, List, Dict
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from fastapi.routing import APIRoute

from app.core.templates import templates
from app.core.database import get_db
from app.modules.permissions import service, schema
from app.modules.permissions.model import Permission
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_permissions(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    # 1. Fetch existing permissions from the database for correlation
    db_permissions = service.get_permissions(db)
    # SQLAlchemy columns must be explicitly checked against None
    permission_lookup: dict[str, Permission] = {
        str(p.codename): p
        for p in db_permissions
    }    
    seen_codenames: set[str] = set()

    # 2. Dynamically extract registered routes and "wire" them to database records
    endpoints: List[Dict[str, Any]] = []
    
    # Safely access routes
    routes = getattr(request.app, "routes", [])
    
    for route in routes:
        # We primarily care about APIRoute instances which represent our functional endpoints
        if isinstance(route, APIRoute):
            # Skip internal FastAPI/OpenAPI utility routes and static assets
            if route.path in ["/openapi.json", "/docs", "/redoc"] or "/static" in route.path:
                continue

            # Use the route name if provided, otherwise the function name
            codename: str = str(route.name or getattr(route.endpoint, "__name__", "unnamed_route"))
            seen_codenames.add(codename)
            db_record: Optional[Permission] = permission_lookup.get(codename)

            # Determine display name
            display_name = codename.replace("_", " ").replace("-", " ").title()
            # Explicitly check SQLAlchemy column against None
            if db_record is not None:
                display_name = db_record.name
            endpoints.append({
                "name": display_name,
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
            "permissions": endpoints,
            "endpoints": endpoints,
            "theme": theme,
            "user": current_user
        }
    )

@router.post("/sync")
async def sync_permissions(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    # 1. Fetch existing permissions to avoid duplicates
    db_permissions = service.get_permissions(db)
    permission_lookup = {str(p.codename): p for p in db_permissions}
    
    # 2. Discover and Register Routes
    routes = getattr(request.app, "routes", [])
    for route in routes:
        if isinstance(route, APIRoute):
            # Skip internal and static utility routes
            if route.path in ["/openapi.json", "/docs", "/redoc"] or "/static" in route.path:
                continue
                
            codename = str(route.name or getattr(route.endpoint, "__name__", "unnamed_route"))
            if codename not in permission_lookup:
                display_name = codename.replace("_", " ").replace("-", " ").title()
                permission_in = schema.PermissionCreate(
                    name=display_name,
                    codename=codename,
                    description=f"Auto-generated permission for {route.path}"
                )
                service.create_permission(db, permission_in)
                
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/permissions/"}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_permission_page(
    request: Request,
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="permissions/templates/create-permission.html",
        context={"theme": theme, "user": current_user}
    )

@router.post("/create")
async def create_permission(
    name: Annotated[str, Form(...)],
    codename: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    permission_in = schema.PermissionCreate(name=name, codename=codename, description=description)
    service.create_permission(db, permission_in)
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/permissions/"}
    )

@router.get("/{permission_id}/edit", response_class=HTMLResponse)
async def edit_permission_page(
    permission_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
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
    name: Annotated[str, Form(...)],
    codename: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    permission_in = schema.PermissionUpdate(name=name, codename=codename, description=description)
    service.update_permission(db, permission_id, permission_in)
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/permissions/"}
    )

@router.delete("/{permission_id}")
async def delete_permission(
    permission_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_permission(db, permission_id)
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/permissions/"}
    )
