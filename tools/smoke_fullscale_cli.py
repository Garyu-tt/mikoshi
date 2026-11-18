"""Command-line wrapper for explicit full-resolution R239 verification."""
import argparse
import json
import os
from smoke_r239_fullscale_r13 import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--width', type=int, default=920)
    parser.add_argument('--height', type=int, default=920)
    parser.add_argument('--passes', type=int, default=5)
    parser.add_argument('--before', type=int, default=7)
    parser.add_argument('--after', type=int, default=13)
    options = parser.parse_args()
    source = os.getenv('MIKOSHI_RETINA_LEGACY_DIR')
    if not source:
        parser.error('MIKOSHI_RETINA_LEGACY_DIR must point to pinned source')
    print(json.dumps(run(source, options.width, options.height,
                         options.passes, options.before, options.after), sort_keys=True))


if __name__ == '__main__':
    main()
