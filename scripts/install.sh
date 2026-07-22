SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# runtime
pip install \
  -e runtime/api \
  -e runtime/engine \
  -e runtime/boot \
  -e runtime/store \
  -e runtime/transport \
  -e runtime/llm \
  -e runtime/y5ncore-base \
  -e runtime/y5ncore-runtime

# sdk
pip install \
  -e sdk/python

# repos
pip install \
  -e repos/y5napp-system \
  -e repos/y5napp-ident

# apps
pip install \
  -e apps/y5napp-console \
  -e apps/y5napp-runtime \
  -e apps/y5napp-textual \
  -e apps/y5napp-web
