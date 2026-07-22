SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

pip install \
  -e runtime/api \
  -e runtime/engine \
  -e runtime/store \
  -e runtime/transport \
  -e runtime/llm \
  -e runtime/boot \
  -e runtime/y5ncore-base \
  -e sdk/python \
  -e repos/y5napp-system \
  -e repos/y5napp-ident \
  -e apps/y5napp-console \
  -e apps/y5napp-runtime \
  -e apps/y5napp-textual \
  -e apps/y5napp-web
