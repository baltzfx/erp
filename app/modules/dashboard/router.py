from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.api.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, current_user = Depends(get_current_user)):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="dashboard/templates/dashboard.html",
        context={
            "theme": theme,
            "user": current_user
        }
    )
