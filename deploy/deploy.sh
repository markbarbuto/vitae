#!/usr/bin/env bash
# Ships the code, knowledge and config to the VM and rebuilds the stack there. Run from the repo root:
#   bash deploy/deploy.sh [service...]
# With no services it starts all of them, which puts the assistant live behind Caddy.
set -euo pipefail

host=vitae-oracle
python -m uv export --frozen --no-dev --no-emit-project --quiet -o deploy/requirements.txt

ssh "$host" 'mkdir -p ~/vitae/models'
tar czf - --exclude=deploy/.env src knowledge config pyproject.toml uv.lock deploy | ssh "$host" 'tar xzf - -C ~/vitae'
for model in models/Qdrant--bge-small-en-v1.5-onnx-Q-aa8f8b06 models/Xenova--ms-marco-MiniLM-L-6-v2-a0914435; do
  if ! ssh "$host" "test -d ~/vitae/$model"; then
    tar czf - "$model" | ssh "$host" 'tar xzf - -C ~/vitae'
  fi
done

ssh "$host" 'cd ~/vitae/deploy && if [ ! -f .env ]; then
  umask 077
  printf "VITAE_EDGE_SECRET=%s\nVITAE_EVAL_SECRET=%s\n" "$(openssl rand -hex 32)" "$(openssl rand -hex 32)" > .env
fi'
ssh "$host" "cd ~/vitae/deploy && docker compose up -d --build $*"
ssh "$host" 'cd ~/vitae/deploy && docker compose ps'
