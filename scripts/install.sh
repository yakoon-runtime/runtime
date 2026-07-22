SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

# runtime
pip install \
  -e runtime/api \
  -e runtime/engine \
  -e runtime/y5ncore-base \
  -e runtime/y5ncore-runtime \
  -e runtime/y5ncore-llm

# sdk
pip install \
  -e sdk/python

# transport
pip install \
  -e transports/y5ntrans-ws

# storage
pip install \
  -e stores/y5nstore-event \
  -e stores/y5nstore-sequence

# repos (bundles) are source trees, referenced via pythonpath in pyproject.toml

# apps
pip install \
  -e apps/y5napp-console \
  -e apps/y5napp-runtime \
  -e apps/y5napp-textual \
  -e apps/y5napp-web

