"""CLI for the shared, cross-platform process ownership policy."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from infrastructure.processes import load_record, members as owned_members, start, stop


def members(record):
    return [process.pid for process in owned_members(record)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'stop', 'status'])
    parser.add_argument('record', type=Path)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == 'status':
        record = load_record(args.record)
        raise SystemExit(0 if record and members(record) else 1)
    if args.action == 'stop':
        stop(args.record)
    else:
        root = args.record.resolve().parent.parent
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        process = start(args.record, root, root / '.devstack/logs' / (args.record.stem + '.log'), command)
        print(f'started pid={process.pid}')
