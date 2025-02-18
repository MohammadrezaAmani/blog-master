import argparse
import os
from typing import List


def parse_args():
    parser = argparse.ArgumentParser(description="Generate FastAPI boilerplate code.")
    parser.add_argument("name", type=str, help="Name of the directory or file.")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the directory (default: current directory).",
    )
    parser.add_argument("model_names", nargs="*", help="List of model names.")
    parser.add_argument(
        "--mode",
        choices=["w", "a"],
        default="a",
        help="Mode: 'w' for write or 'a' for append (default: a).",
    )
    return parser.parse_args()


def create_directory_structure(base_path: str):
    os.makedirs(base_path, exist_ok=True)
    api_root = os.path.join(base_path, "api")
    os.makedirs(api_root, exist_ok=True)
    return api_root


def generate_init_file(name: str, model_names: List[str], base_path: str, mode: str):
    class_names = generate_table_names(model_names)
    scheme_names = [
        f"{name}{suffix}"
        for name in class_names
        for suffix in ("CreateScheme", "ResponseScheme")
    ]

    class_name_imports = ",".join(class_names)
    scheme_name_imports = ",".join(scheme_names)
    all_class_name_imports = ",".join([f'"{name}"' for name in class_names])
    all_scheme_name_imports = ",".join([f'"{name}"' for name in scheme_names])

    with open(os.path.join(base_path, "__init__.py"), mode=mode) as f:
        f.write(
            f"""
from .model import {class_name_imports}
from .scheme import ({scheme_name_imports})

__all__ = [
{all_class_name_imports},
{all_scheme_name_imports},
]
"""
        )


def generate_table_names(model_names: List[str], seperate: bool = False) -> List[str]:
    return [
        (
            name.replace("_", " ").title()
            if seperate
            else name.replace("_", " ").title().replace(" ", "").replace("_", "")
        )
        for name in model_names
    ]


def generate_model_files(model_names: List[str], base_path: str, mode: str):
    table_names = generate_table_names(model_names)
    with open(os.path.join(base_path, "model.py"), mode=mode) as f:
        f.write("from tortoise import fields\n\nfrom src.base import BaseModel\n")
        for model_name, table_name in zip(table_names, model_names):
            f.write(
                f"""
class {model_name}(BaseModel):
    def __repr__(self):
        return self.__str__()

    class Meta:
        table = "{table_name.lower()}"
"""
            )


def generate_schemas(
    model_names: List[str],
    base_path: str,
    mode: str,
):
    model_names = generate_table_names(model_names)
    with open(os.path.join(base_path, "scheme.py"), mode=mode) as f:
        f.write(
            """from src.base.scheme import BaseCreateScheme, BaseResponseScheme\n"""
        )
        for scheme_name in model_names:
            f.write(f"class {scheme_name}CreateScheme(BaseCreateScheme):...\n\n")
            f.write(
                f"class {scheme_name}ResponseScheme({scheme_name}CreateScheme, BaseResponseScheme):...\n\n"
            )


def generate_api_files(name: str, model_names: List[str], base_path: str, mode: str):
    table_names = generate_table_names(model_names)
    for model_name, model_title in zip(model_names, table_names):
        with open(os.path.join(base_path, "api", f"{model_name}.py"), mode=mode) as f:
            f.write(
                f"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from src.app.{name} import {model_title}, {model_title}CreateScheme, {model_title}ResponseScheme
from src.helper import (
    ActionEnum,
    Filter,
    OrderBy,
    Paginated,
    Paginator,
    Status,
    create_filter_schema,
    has_access,
    log_action,
    login_required,
)
from src.helper.user.model import User
from tortoise.queryset import Q

router = APIRouter()

{model_title}FilterSchema = create_filter_schema({model_title})

MODEL_NAME: str = {model_title}._meta.db_table

@router.get("/", response_model=Paginated[{model_title}ResponseScheme] | List[{model_title}ResponseScheme])
@log_action(action=ActionEnum.VIEW_ALL.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW_ALL.value, to=MODEL_NAME)
async def get_{model_name}s_router(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    filters: {model_title}FilterSchema = Depends(),  # type: ignore
    user: User=Depends(login_required),
    sort_by: list[str] = Query([]),
    pagination: bool = Query(True),
):
    objects = {model_title}.all()
    sort = OrderBy.create(objects, sort_by)
    objects = Filter.create(sort, filters)
    return await Paginator(limit=limit, page=page).paginated(
        {model_title}ResponseScheme, objects, apply=pagination
    )

@router.post("/", response_model={model_title}ResponseScheme)
@log_action(action=ActionEnum.CREATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.CREATE.value, to=MODEL_NAME)
async def create_{model_name}_router(
    object: {model_title}CreateScheme,
    user: User=Depends(login_required),
):
    return await object.create(
        {model_title},
        serialize=True,
        serializer={model_title}ResponseScheme,
        m2m=[],
    )
"""
                + """
@router.get("/{id}","""
                + f"""response_model={model_title}ResponseScheme)
@log_action(action=ActionEnum.VIEW.value, model=MODEL_NAME)
@has_access(action=ActionEnum.VIEW.value, to=MODEL_NAME)
async def get_{model_name}_router(
    id: str,
    request: Request,
    user: User=Depends(login_required),
):
    objects = {model_title}.all()
    return await {model_title}ResponseScheme.from_tortoise_orm({model_title}ResponseScheme, await objects.get(Q(id=id) if str(id).isdigit() else Q(slug=str(id))))

"""
                + """
@router.put("/{id}","""
                + f""" response_model={model_title}ResponseScheme)
                
@log_action(action=ActionEnum.UPDATE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.UPDATE.value, to=MODEL_NAME)
async def update_{model_name}_router(
    id: int,
    object: {model_title}CreateScheme,
    user: User=Depends(login_required),
):
    objects = {model_title}.all()
    return await object.update(
        await objects.get(id=id),
        serialize=True,
        serializer={model_title}ResponseScheme,
        m2m=[],
    )"""
                + """
@router.delete("/{id}", response_model=Status)
"""
                + f"""
@log_action(action=ActionEnum.DELETE.value, model=MODEL_NAME)
@has_access(action=ActionEnum.DELETE.value, to=MODEL_NAME)
async def delete_{model_name}_router(id: int, user: User = Depends(login_required)):
    objects = {model_title}.filter().all()
    deleted_count = await objects.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"{model_title}"""
                + """ {id} not found")"""
                + f"""
    return Status(message=f"Deleted {model_name}"""
                """ {id}")
"""
            )


def generate_api_init(name: str, model_names: List[str], base_path: str, mode: str):
    table_names = generate_table_names(model_names, seperate=True)
    with open(os.path.join(base_path, "api", "__init__.py"), mode=mode) as f:
        f.write("from fastapi import APIRouter\n")
        for model_name in model_names:
            f.write(
                f"from src.app.{name}.api.{model_name} import router as {model_name}_router\n"
            )
        f.write("from src.helper import add_patterns\n\napi_patterns = [\n")
        for model_name, table_name in zip(model_names, table_names):
            f.write(
                f"    ({model_name}_router, '/{model_name}', ['{table_name}'], {{}}),\n"
            )
        f.write("\n]\n\nrouter = add_patterns(APIRouter(), api_patterns)\n")


def run_codebase_formatter():
    os.system("isort . --profile=black; black .; ruff format .;")


def main():
    args = parse_args()

    base_path = os.path.join(args.path, args.name)
    model_names = args.model_names
    mode = args.mode

    create_directory_structure(base_path)
    generate_init_file(args.name, model_names, base_path, mode)
    generate_model_files(model_names, base_path, mode)
    generate_schemas(model_names, base_path, mode)
    generate_api_files(args.name, model_names, base_path, mode)
    generate_api_init(args.name, model_names, base_path, mode)
    run_codebase_formatter()


if __name__ == "__main__":
    main()
