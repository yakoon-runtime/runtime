
import yaml

from yakoon.base.stores.boot.base.router import MigratorRouter


async def migrate_from_config(path: str):

    with open(path) as f:
        config = yaml.safe_load(f)

    router = MigratorRouter(config)
    await router.run()

    print(f"✅ Migration finished: {path}")
