cd ..

# platform
pip install \
  -e platform/yakoon-core-base \
  -e platform/yakoon-core-compose \
  -e platform/yakoon-core-platform \

# hosts
pip install \
  -e hosts/yakoon-host-console \

# transport
pip install \
  -e transport/yakoon-transport-ws \

# plugins
pip install \
  -e plugins/yakoon-crm \
  -e plugins/yakoon-office \
  -e plugins/yakoon-playground \
  -e plugins/yakoon-shell \

# clients
pip install \
  -e clients/yakoon-client-console \

# apps
pip install \
  -e apps/yakoon-app-console \
  -e apps/yakoon-app-ssh \
  -e apps/yakoon-app-web \
