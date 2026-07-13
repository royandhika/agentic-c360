import dagster as dg

from . import assets
from .resources import MinIOResource, PostgresResource, SFTPSourceResource, VendorApiResource

landing_assets = dg.load_assets_from_package_module(assets)
landing_checks = dg.load_asset_checks_from_package_module(assets)

defs = dg.Definitions(
    assets=landing_assets,
    asset_checks=landing_checks,
    resources={
        "postgres": PostgresResource(),
        "minio": MinIOResource(),
        "vendor_api": VendorApiResource(),
        "crm_sftp": SFTPSourceResource(),
    },
)
