cd ..

# platform
pip install \
  -e platform/yakoon-core-base \
  -e platform/yakoon-core-compose \
  -e platform/yakoon-core-platform \

# hosts
pip install \
  -e hosts/yakoon-host-console \
  -e hosts/yakoon-host-ws \
  -e hosts/yakoon-host-kivy \

# extensions
pip install \
  -e exts/yakoon-shell \

# apps
pip install \
  -e apps/yakoon-crm \
  -e apps/yakoon-office \
  -e apps/yakoon-playground \
