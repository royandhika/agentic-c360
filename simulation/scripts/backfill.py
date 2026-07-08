#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timedelta

import click
import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(SCRIPT_DIR)
PROJ_DIR = os.path.dirname(SIM_DIR)
sys.path.insert(0, SIM_DIR)
sys.path.insert(0, os.path.join(SIM_DIR, 'gen'))

from generator import DailyGenerator


@click.command()
@click.option('--days', required=True, type=int, help='Number of days to backfill.')
@click.option('--start', default=None, help='Start date (YYYY-MM-DD). Default: today - N days.')
@click.option('--holiday', is_flag=True, help='Generate every day at holiday-mode spike volume.')
def main(days, start, holiday):
    config_path = os.path.join(SIM_DIR, 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    config['holiday_mode'] = holiday

    if start:
        begin = datetime.strptime(start, '%Y-%m-%d').date()
    else:
        begin = datetime.today().date() - timedelta(days=days)

    gen = DailyGenerator(config)
    try:
        for i in range(days):
            day = begin + timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')

            if gen.world.was_generated(date_str):
                print(f"[{i + 1}/{days}] {date_str} - skipped")
                continue

            gen.generate(date_str, holiday_mode=holiday)
            print(f"[{i + 1}/{days}] {date_str} - generated" + (" (holiday)" if holiday else ""))
    finally:
        gen.close()


if __name__ == '__main__':
    main()
