#!/usr/bin/env python3
import os
import sys
import yaml
import click

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(SCRIPT_DIR)
PROJ_DIR = os.path.dirname(SIM_DIR)
sys.path.insert(0, SIM_DIR)
sys.path.insert(0, os.path.join(SIM_DIR, 'gen'))

from generator import DailyGenerator


@click.command()
@click.option('--date', required=True, help='Date to generate (YYYY-MM-DD).')
@click.option('--holiday', is_flag=True, help='Generate at holiday-mode spike volume.')
def main(date, holiday):
    config_path = os.path.join(SIM_DIR, 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    config['holiday_mode'] = holiday

    gen = DailyGenerator(config)
    try:
        gen.generate(date, holiday_mode=holiday)
        print(f"Generated travel day {date}" + (" (holiday mode)" if holiday else ""))
    finally:
        gen.close()


if __name__ == '__main__':
    main()
