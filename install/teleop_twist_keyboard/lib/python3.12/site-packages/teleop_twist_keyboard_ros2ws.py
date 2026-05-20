#!/usr/bin/env python3

from pathlib import Path
import runpy


def main():
    script_path = Path(__file__).resolve().parent / 'teleop_twist_keyboard' / 'teleop_twist_keyboard.py'
    runpy.run_path(str(script_path), run_name='__main__')


if __name__ == '__main__':
    main()