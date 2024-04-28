from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from . import assets

all_assets = load_assets_from_modules([assets])

# Define a job that will materialize the assets
et_job = define_asset_job("etl_job", selection=AssetSelection.all())

# Addition: a ScheduleDefinition the job it should run and a cron schedule of how frequently to run it
etl_schedule = ScheduleDefinition(
    job=et_job,
    cron_schedule="0 13 * * *",  # Daily at 1 PM
)

defs = Definitions(
    assets=all_assets,
    schedules=[etl_schedule],
)




'''
from dagster import Definitions, load_assets_from_modules

from . import assets

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
)
'''