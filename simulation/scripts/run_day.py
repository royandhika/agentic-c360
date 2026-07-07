#!/usr/bin/env python3
"""Generate one retail day of Indonesian data across all three mock sources."""

import os
import sys
import click
import yaml

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SIM_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _SIM_DIR)
sys.path.insert(0, os.path.join(_SIM_DIR, 'src'))

from gen.generator import DailyGenerator


@click.command()
@click.option('--date', required=True, help='Business date in YYYY-MM-DD format')
@click.option('--holiday', is_flag=True, help='Apply holiday uplift multiplier')
def main(date, holiday):
    """Generate one retail day of Indonesian data."""
    config_path = os.path.join(_SIM_DIR, 'config.yaml')
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config['holiday_mode'] = holiday

    gen = DailyGenerator(config)
    try:
        gen.generate(date, holiday_mode=holiday)
        click.echo(f"Generated {date}, holiday={holiday}")
    finally:
        gen.close()


if __name__ == '__main__':
    main()
