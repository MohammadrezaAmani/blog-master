#!/bin/bash

REPO_URL="git@192.168.10.44:oghaf/backend.git"
BRANCH="main"

PROJECT_DIR="./oghaf_backend"

if [ ! -d "$PROJECT_DIR" ]; then
  git clone "$REPO_URL" "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

pip install -r requirements.txt

killall uvicorn

uvicorn src:app --host 0.0.0.0 --port 5885 --reload
