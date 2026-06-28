cd ..

# runtime 
pip install \
  -e runtime/y5ncore-base \
  -e runtime/y5ncore-runtime \
  -e runtime/y5ncore-llm \

# transport
pip install \
  -e transports/y5ntrans-ws \

# storage
pip install \
  -e stores/y5nstore-event \
  -e stores/y5nstore-sequence \

# spaces
pip install \
  -e spaces/y5nspace-shell \
  -e spaces/y5nspace-runtime \
  -e spaces/y5nspace-ident \
  -e spaces/y5nspace-os \
  -e spaces/y5nspace-crm \

# apps
pip install \
  -e apps/y5napp-console \
  -e apps/y5napp-runtime \
  -e apps/y5napp-textual \
  -e apps/y5napp-web \

