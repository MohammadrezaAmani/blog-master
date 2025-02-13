from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from src.config.util import get_user_model
from src.helper.auth import login_required
from src.helper.filters import create_filter_schema
from src.helper.logger import ActionEnum, Log, log_action
from src.helper.select import Select

router = APIRouter()

LogFilterSchema = create_filter_schema(Log, ["last_value"])

UserModel = get_user_model()


@router.get("/")
@log_action(action=ActionEnum.VIEW.value, model="Logs", user_field="cuser")
async def get_logs(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: LogFilterSchema = Depends(),  # type: ignore
    cuser=Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    return {}


@router.get("/{log_id}")
@log_action(action=ActionEnum.VIEW.value, model="Logs", model_id_field="log_id")
async def get_log(
    log_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: LogFilterSchema = Depends(),  # type: ignore
    user=Depends(login_required),
    select: list[str] = Query(None),
):
    if not user:
        return RedirectResponse(f"/login?next=/api/logs/{log_id}")
    return Select.create(await Log.get(pk=log_id), select, model=Log)
