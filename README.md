# BIONEX-Backend

## running project

```shell
./venv/bin/python -m uvicorn src:app --reload --host 0.0.0.0
```

## installing requirements

```shell
./venv/bin/python -m pip install -r requirements.txt
```

## creating apps

```shell
python ./src/bases/create_app.py dim ./src/apps organ region
```

## Pre-commit

```shell
pip install pre-commit
```

```shell
pre-commit install
```
