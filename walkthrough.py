"""Guided runnable patterns. These checks use only disposable databases.

Run baseline before editing, or finished after completing Store. Read
WALKTHROUGH.md for what each observation means and what it leaves unchecked.
"""
import argparse
import json
import signal
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory

from capstone_harness import LocalService, show
from failed_write_check import snapshot
from store import Store

DESTINATION = "https://example.org/guide/setup"


def expect(response, status):
    assert response['status'] == status, response


def clicks(service, code):
    response = service.request('GET', '/stats/' + code)
    expect(response, 200)
    return json.loads(response['body'])['clicks']


def baseline():
    with TemporaryDirectory(prefix='link-baseline-') as folder:
        database = Path(folder) / 'baseline.sqlite3'
        with LocalService(Store(database)) as service:
            response = service.request('GET', '/health')
            expect(response, 200)
            assert json.loads(response['body']) == {'status': 'ok'}
            show('Health', response)
            for method, path, data, client, name in [
                ('POST', '/links', {'code': 'lesson', 'destination': DESTINATION}, None, 'create'),
                ('GET', '/stats/lesson', None, None, 'stats'),
                ('GET', '/s/lesson', None, 'reader_a', 'resolve'),
            ]:
                response = service.request(method, path, data, client)
                expect(response, 501)
                assert json.loads(response['body']) == {
                    'error': 'Complete Store.' + name + ' using CONTRACT.md'}
                show('Unfinished ' + name, response)
        assert not service.thread.is_alive()
        show('HTTP thread stopped', True)
    assert not database.exists()
    show('Temporary database removed', True)


def ordinary_and_boundary():
    with TemporaryDirectory(prefix='link-ordinary-') as folder:
        database = Path(folder) / 'ordinary.sqlite3'
        now = [179.999]
        with LocalService(Store(database), clock=lambda: now[0]) as service:
            expect(service.request('POST', '/links', {
                'code': 'lesson', 'destination': DESTINATION}), 201)
            for _ in range(5):
                response = service.request('GET', '/s/lesson', client='reader_a')
                expect(response, 302)
                assert response['headers'].get('Location') == DESTINATION
                assert response['body'] == ''
            expect(service.request('GET', '/s/lesson', client='reader_a'), 429)
            assert clicks(service, 'lesson') == 5
            show('Before boundary', snapshot(database))
            now[0] = 180
            expect(service.request('GET', '/s/lesson', client='reader_a'), 302)
            assert clicks(service, 'lesson') == 6
            state = snapshot(database)
            assert state['buckets']['rows'] == [['reader_a', 120, 5], ['reader_a', 180, 1]]
            show('At boundary', state)
        assert not service.thread.is_alive()
    assert not database.exists()
    show('Ordinary example cleaned up', True)


def parallel():
    with TemporaryDirectory(prefix='link-parallel-') as folder:
        database = Path(folder) / 'parallel.sqlite3'
        with LocalService(Store(database), clock=lambda: 120) as service:
            for code in ('alpha', 'beta'):
                expect(service.request('POST', '/links', {
                    'code': code, 'destination': DESTINATION}), 201)
            ready = threading.Barrier(12, timeout=15)

            def call(number):
                code = 'alpha' if number % 2 == 0 else 'beta'
                ready.wait()
                return service.request('GET', '/s/' + code, client='reader_a')

            with ThreadPoolExecutor(max_workers=12) as pool:
                replies = list(pool.map(call, range(12)))
            statuses = [response['status'] for response in replies]
            assert statuses.count(302) == 5 and statuses.count(429) == 7, statuses
            for response in replies:
                if response['status'] == 302:
                    assert response['headers'].get('Location') == DESTINATION
                    assert response['body'] == ''
                else:
                    assert 'Location' not in response['headers']
            counts = {code: clicks(service, code) for code in ('alpha', 'beta')}
            assert sum(counts.values()) == 5, counts
            state = snapshot(database)
            assert state['buckets']['rows'] == [['reader_a', 120, 5]], state
            show('Parallel statuses', statuses)
            show('Parallel counts', counts)
            show('Parallel saved state', state)
        assert not service.thread.is_alive()
    assert not database.exists()
    show('Parallel example cleaned up', True)


class ProcessService:
    """Start the actual command-line server at one chosen time, then stop it."""
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        self.process = subprocess.Popen([
            sys.executable, '-u', str(Path(__file__).with_name('server.py')),
            '--database', str(self.database), '--port', '0', '--test-clock', '120',
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            line = self.process.stdout.readline()
            if not line.startswith('Local service: http://127.0.0.1:'):
                raise RuntimeError('Server did not start: ' + line)
            self.port = int(line.strip().rsplit(':', 1)[1])
            return self
        except BaseException:
            self.stop()
            raise

    def request(self, method, path, data=None, client=None):
        connection = HTTPConnection('127.0.0.1', self.port, timeout=10)
        headers = {} if client is None else {'X-Client-Id': client}
        body = None if data is None else json.dumps(data)
        try:
            connection.request(method, path, body, headers)
            response = connection.getresponse()
            return {'status': response.status, 'headers': dict(response.getheaders()),
                    'body': response.read().decode('utf-8')}
        finally:
            connection.close()

    def stop(self):
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
        try:
            output, errors = self.process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.communicate()
            raise RuntimeError('Server did not stop after the interrupt')
        assert self.process.returncode == 0, (self.process.returncode, output, errors)
        show('Server process stopped cleanly', self.process.returncode)

    def __exit__(self, *error):
        self.stop()


def restart():
    with TemporaryDirectory(prefix='link-restart-') as folder:
        database = Path(folder) / 'restart.sqlite3'
        with ProcessService(database) as service:
            expect(service.request('POST', '/links', {
                'code': 'lesson', 'destination': DESTINATION}), 201)
            for _ in range(2):
                expect(service.request('GET', '/s/lesson', client='reader_a'), 302)
            assert clicks(service, 'lesson') == 2
            before = snapshot(database)
            show('Before process stop', before)
        with ProcessService(database) as service:
            assert clicks(service, 'lesson') == 2
            assert snapshot(database) == before
            for _ in range(3):
                expect(service.request('GET', '/s/lesson', client='reader_a'), 302)
            expect(service.request('GET', '/s/lesson', client='reader_a'), 429)
            assert clicks(service, 'lesson') == 5
            show('After process restart', snapshot(database))
    assert not database.exists()
    show('Restart example cleaned up', True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['baseline', 'finished'])
    args = parser.parse_args()
    if args.mode == 'baseline':
        baseline()
    else:
        ordinary_and_boundary()
        parallel()
        restart()
        from failed_write_check import run_check
        run_check()
        show('Guided checks', 'PASS')
