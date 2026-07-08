import dagster as dg

from . import assets

landing_assets = dg.load_assets_from_package_module(assets, group_name="landing")

defs = dg.Definitions(assets=landing_assets)
