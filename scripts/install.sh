cd ..

# runtime (base)
pip install \
  -e runtime/y5ncore-base \

# storage
pip install \
  -e stores/y5nstore-event \

# runtime (runtime)
pip install \
  -e runtime/y5ncore-runtime \

# transport
pip install \
  -e transports/y5ntrans-ws \

# spaces
pip install \
  -e spaces/y5nspace-runtime \
  -e spaces/y5nspace-shell \
  -e spaces/y5nspace-ident \

# clients
pip install \
  -e clients/y5ncli-console \
  -e apps/y5napp-textual \

# apps
pip install \
  -e apps/y5napp-console \
  -e apps/y5napp-ssh \
  -e apps/y5napp-web \
