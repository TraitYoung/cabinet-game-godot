"""Check the configured API database mount using disposable containers and a fresh volume.

Run: python scripts/check_container_persistence.py [--sudo]
Never starts the real API/Hindsight or mounts their data volumes.
"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from uuid import uuid4


def check(sudo=False, image=None):
    docker = (['sudo'] if sudo else []) + ['docker', 'compose']
    config = json.loads(subprocess.check_output(docker + ['config', '--format', 'json']))
    api = config['services']['api']
    database = api['environment']['AX_DB_PATH']
    source = next(volume for volume in api['volumes'] if volume['target'] == '/app')
    data = next(volume for volume in api['volumes'] if volume['target'] == str(Path(database).parent))
    assert data['type'] == 'volume'
    isolated = {'services': {'api': {
        'image': image or api['image'], 'working_dir': '/app', 'entrypoint': [], 'user': api.get('user', '0:0'),
        'environment': {'AX_DB_PATH': database},
        'volumes': [{**source, 'read_only': True}, data],
    }}, 'volumes': {data['source']: {}}}
    with tempfile.TemporaryDirectory() as directory:
        compose = Path(directory) / 'compose.json'
        compose.write_text(json.dumps(isolated))
        command = docker + ['-p', 'bina-quality-' + uuid4().hex[:12], '-f', str(compose)]
        setup = '''import os
from storage.chat_history import ChatHistory
from state.mood_engine import MoodEngine
path = os.environ['AX_DB_PATH']
history = ChatHistory(path)
history.append_turn('persistence-check', 'test user', 'test reply')
MoodEngine(path).apply_delta('persistence-check', valence=.4)
'''
        verify = '''import os
from storage.chat_history import ChatHistory
from state.mood_engine import MoodEngine
path = os.environ['AX_DB_PATH']
assert ChatHistory(path).get_turns('persistence-check')[0]['assistant'] == 'test reply'
assert MoodEngine(path).get_state('persistence-check').valence == .4
print('PASS: chat history and mood survived API container replacement')
'''
        try:
            pydantic_pin = next(line for line in Path('requirements.lock.txt').read_text().splitlines() if line.startswith('pydantic=='))
            bootstrap = ("import importlib.util, subprocess, sys\n"
                "if importlib.util.find_spec('pydantic') is None:\n"
                f"    subprocess.run([sys.executable, '-m', 'pip', 'install', {pydantic_pin!r}], check=True)\n")
            for code in (setup, verify):
                subprocess.run(command + ['run', '--rm', '--no-deps', 'api', 'python', '-c', bootstrap + code], check=True)
        finally:
            subprocess.run(command + ['down', '-v'], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sudo', action='store_true')
    parser.add_argument('--image', help='Optional cached Python image for offline storage verification')
    args = parser.parse_args()
    check(args.sudo, args.image)
