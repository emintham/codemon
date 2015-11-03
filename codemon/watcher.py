import os
import sys
import threading
import time


__all__ = ['Watcher']


class BackgroundThread(threading.Thread):
    """BackgroundThread

    Runs a routine continuously in a separate thread until
    `BackgroundThread.cancel` is called.
    """

    def __init__(self, func, frequency=2, verbosity=1, **kwargs):
        super(BackgroundThread, self).__init__(**kwargs)
        self.func = func
        self.frequency = frequency
        self.verbosity = verbosity
        self.daemon = True

    def cancel(self):
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            time.sleep(self.frequency)

            if not self.running:
                return

            try:
                self.func()
            except Exception:
                raise


class Watcher(object):
    """Watcher

    Checks periodically to see if a list of given files have changed and
    passes the list of changed files to a given callback.
    """

    def __init__(self, filenames, callback, verbosity=1, **kwargs):
        self.filenames = filenames
        self.callback = callback
        self.mtimes = {}
        self.verbosity = verbosity
        self.thread = self._create_thread()

    def _create_thread(self):
        return BackgroundThread(self.test_if_changed,
                                verbosity=self.verbosity,
                                name='Watcher thread')

    def start(self):
        self.thread.start()

        if self.verbosity >= 2:
            sys.stdout.write('\n[CODEMON] Watcher is now watching your code...\n')

        try:
            while True:
                time.sleep(2)

                if not self.thread.is_alive():
                    self.thread = self._create_thread()
                    self.thread.start()

        except KeyboardInterrupt:
            sys.exit(0)

    def test_if_changed(self):
        changed_files = []

        for filename in self.filenames:
            if not filename:
                raise Exception('Got a falsy filename!')

            prev_time = self.mtimes.get(filename, 0)
            if prev_time is None:
                continue

            try:
                mtime = os.stat(filename).st_mtime
            except OSError:
                # file deleted
                mtime = None

            if filename not in self.mtimes:
                self.mtimes[filename] = mtime
            elif mtime != self.mtimes[filename]:
                changed_files.append(filename)

        if len(changed_files) > 0:
            self.mtimes = {}
            self.callback(changed_files)
