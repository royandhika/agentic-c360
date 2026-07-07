#!/usr/bin/env python3
"""Backfill N days of Indonesian retail data."""

import os
import sys
from datetime import datetime, timedelta
import click
import yaml

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SIM_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _SIM_DIR)
sys.path.insert(0, os.path.join(_SIM_DIR, 'src'))

from gen.generator import DailyGenerator


@click.command()
@click.option('--days', required=True, type=int, help='Number of days to backfill')
@click.option('--start', default=None, help='Start date YYYY-MM-DD (default: days ago from today)')
@click.option('--holiday', is_flag=True, help='Apply holiday uplift on matching dates')
def main(days, start, holiday):
    """Backfill N days of data."""
    config_path = os.path.join(_SIM_DIR, 'config.yaml')
    with open(config_path) as f:
        config = yaml.safe_load(f)

    if start:
        start_date = datetime.strptime(start, '%Y-%m-%d')
    else:
        start_date = datetime.now() - timedelta(days=days)

    gen = DailyGenerator(config)
    generated = 0
    skipped = 0
    try:
        for i in range(days):
            d = start_date + timedelta(days=i)
            date_str = d.strftime('%Y-%m-%d')
            if gen.world.was_generated(date_str):
                click.echo(f"Skipping {date_str} (already exists)")
                skipped += 1
                continue
            gen.generate(date_str, holiday_mode=holiday)
            generated += 1
            click.echo(f"[{generated}/{days}] {date_str}")
    finally:
        gen.close()

    click.echo(f"Done. Generated: {generated}, Skipped: {skipped}")


if __name__ == '__main__':
    main()
