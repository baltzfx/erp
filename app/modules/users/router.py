from __future__ import annotations
import csv
import io
from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated, Any

from app.core.templates import templates
from app.core.database import get_db
from app.api.deps import get_current_user
from app.modules.users import crud, schema
from app.modules.users.model import User
from app.modules.users.crud import verify_password
from app.modules.roles import service as role_service

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/", response_class=HTMLResponse)
async def users_page(
    request: Request, 
    db: Annotated[Session, Depends(get_db)], 
    current_user: Annotated[User, Depends(get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    users = crud.get_users(db)
    return templates.TemplateResponse(
        request=request,
        name="users/templates/users.html",
        context={
            "theme": theme,
            "users": users,
            "user": current_user
        }
    )

@router.get("/me", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="users/templates/profile.html",
        context={
            "theme": theme,
            "user": current_user
        }
    )

@router.get("/create", response_class=HTMLResponse)
async def create_user_page(
    request: Request, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    roles = role_service.get_roles(db)
    return templates.TemplateResponse(
        request=request,
        name="users/templates/create-user.html",
        context={
            "theme": theme,
            "user": current_user,
            "roles": roles
        }
    )

@router.post("/")
def create_user(
    db: Annotated[Session, Depends(get_db)],
    email: Annotated[str, Form(...)],
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
    first_name: Annotated[Optional[str], Form()] = None,
    last_name: Annotated[Optional[str], Form()] = None,
    role_id: Annotated[Optional[int], Form()] = None,
    is_active: Annotated[bool, Form()] = True,
    is_superuser: Annotated[bool, Form()] = False
):
    if crud.get_user_by_email(db, email=email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_user_by_username(db, username=username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user_in = schema.UserCreate(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_superuser=is_superuser,
        role_id=role_id
    )
    crud.create_user(db=db, user=user_in)
    
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/users/"}
    )

@router.get("/api", response_model=List[schema.UserOut])
def read_users(db: Annotated[Session, Depends(get_db)], skip: int = 0, limit: int = 100):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schema.UserOut)
def read_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/{user_id}/view", response_class=HTMLResponse)
async def view_user_page(
    user_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="users/templates/view-user.html",
        context={"theme": theme, "target_user": db_user, "user": current_user}
    )

@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_page(
    user_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    theme = request.cookies.get("theme", "light")
    roles = role_service.get_roles(db)
    return templates.TemplateResponse(
        request=request,
        name="users/templates/edit-user.html",
        context={
            "theme": theme, 
            "target_user": db_user, 
            "user": current_user,
            "roles": roles
        }
    )

@router.post("/{user_id}/edit")
async def update_user(
    user_id: int, 
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    email: Annotated[str, Form(...)],
    username: Annotated[str, Form(...)],
    password: Annotated[Optional[str], Form()] = None,
    first_name: Annotated[Optional[str], Form()] = None,
    last_name: Annotated[Optional[str], Form()] = None,
    role_id: Annotated[Optional[int], Form()] = None,
    is_active: Annotated[bool, Form()] = True,
    is_superuser: Annotated[bool, Form()] = False
) -> JSONResponse:
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    user_data = schema.UserUpdate(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role_id=role_id,
        is_active=is_active,
        is_superuser=is_superuser
    )
    
    db_user = crud.update_user(db, user_id=user_id, user=user_data)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/users/"}
    )

@router.post("/bulk-delete")
def bulk_delete_users(
    request: schema.BulkDeleteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, Any]:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Prevent self-deletion in bulk
    ids_to_delete = [uid for uid in request.user_ids if uid != current_user.id]
    count = crud.delete_users_bulk(db, ids_to_delete)
    return {"status": "success", "deleted": count}

@router.post("/me/password")
def change_my_password(
    data: schema.PasswordChange,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, Any]:
    if not data.old_password or not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    crud.update_password(db, current_user.id, data.new_password)
    return {"status": "success", "message": "Password updated"}

@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    data: schema.PasswordChange,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> dict[str, Any]:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    if crud.update_password(db, user_id, data.new_password):
        return {"status": "success", "message": "User password reset successfully"}
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/export/list")
def export_users(db: Annotated[Session, Depends(get_db)]):
    users = crud.get_users(db, limit=1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "username", "first_name", "last_name", "is_active", "is_superuser"])
    
    for u in users:
        writer.writerow([u.id, u.email, u.username, u.first_name or "", u.last_name or "", u.is_active, u.is_superuser])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )

@router.get("/export/template")
def export_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["email", "username", "password", "first_name", "last_name", "is_active", "is_superuser"])
    writer.writerow(["test@example.com", "testuser", "securepass123", "John", "Doe", "True", "False"])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=user_import_template.csv"}
    )

@router.post("/import")
async def import_users(
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...)
) -> JSONResponse:
    content = await file.read()
    try:
        stream = io.StringIO(content.decode("utf-8"))
    except UnicodeDecodeError:
        stream = io.StringIO(content.decode("latin-1"))
        
    reader = csv.DictReader(stream)
    
    imported_count = 0
    errors: list[str] = []
    
    for row in reader:
        try:
            # Handle missing passwords (e.g. when importing from an export file)
            password = row.get('password')
            if not password:
                password = "Password123!"

            user_in = schema.UserCreate(
                email=row['email'],
                username=row['username'],
                password=password,
                first_name=row.get('first_name'),
                last_name=row.get('last_name'),
                is_active=row.get('is_active', 'True').lower() == 'true',
                is_superuser=row.get('is_superuser', 'False').lower() == 'true'
            )
            if not crud.get_user_by_email(db, email=user_in.email):
                crud.create_user(db, user_in)
                imported_count += 1
        except Exception as e:
            errors.append(f"Error importing {row.get('email')}: {str(e)}")
            
    return JSONResponse(
        content={"status": "success", "imported": imported_count, "errors": errors},
        headers={"HX-Redirect": "/users/"}
    )

@router.delete("/{user_id}", response_model=schema.UserOut)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
