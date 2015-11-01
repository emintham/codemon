import itertools
import sys

from coverage import Coverage

import msgpack

from .watcher import Watcher
from .config import Config, ConfigParser
from .datastructures import SourceMap


__all__ = ['InfluenceMapper', 'Codemon']


spinner = itertools.cycle(['-', '\\', '|', '/'])


class InfluenceMapper(object):
    """InfluenceMapper

    Computes the influence each LOC has on each test.

    A LOC influences a test if the test goes through that LOC when the test is
    being run.

    Users should subclass this and implement their own ``index_tests``,
    ``map_test``, and ``test_suite``. See below for the signatures of these
    methods.

    Users can also optionally implement `setup` or `cleanup` to perform any
    required setup and/or cleanups before/after `run` respectively.
    """

    def __init__(self, config=None, source_map_file='.codemonmap',
                 use_cached=False, verbosity=1):
        assert isinstance(config, Config)

        self.config = config
        self._tests = None
        self.source_map = self.read_from_file(source_map_file)
        self.use_cached = use_cached
        self.verbosity = verbosity

    def read_from_file(self, filename):
        try:
            with open(filename, 'rb') as f:
                source_map = msgpack.unpackb(f.read())

            return SourceMap(source_map)
        except (IOError, EOFError):
            return SourceMap()

    def setup(self):
        """Hook to perform any optional setup before running."""
        pass

    def cleanup(self):
        """Hook to perform any optional cleanup after running."""
        pass

    def index_tests(self):
        """Hook to run indexer"""
        raise NotImplementedError(
            'Subclasses should implement {}'.format(self.__name__)
        )

    def run_affected_tests(self, filenames):
        # TODO: finer granularity
        suite = self.source_map.suite(filenames)

        if self.verbosity >= 2:
            output_message = '\nThe following files have changed:\n'
            output_message += '\n'.join(filenames)
            output_message += '\nRunning the following tests:\n'
            output_message += '\n'.join(suite)

            sys.stdout.write(output_message.format(filenames) + '\n')

        self.test_suite(suite)

    def test_suite(self, suite):
        """
        Hook to perform a test on change. `suite` will be a set of strings
        where each string is the absolute path of a test.
        """
        raise NotImplementedError(
            'Subclasses should implement {}'.format(self.__name__)
        )

    def filter_omitted_tests(self, tests):
        suite = []

        for test_name in tests:
            if self.config.is_omitted_test(test_name):
                continue
            suite.append(test_name)

        return suite

    @property
    def tests(self):
        tests = self._tests or self.index_tests()
        return self.filter_omitted_tests(tests)

    def map_test(self, test_name):
        """Hook to run a single test to compute its influence"""
        raise NotImplementedError(
            'Subclasses should implement {}'.format(self.__name__)
        )

    def run_coverage(self, test_name):
        cov = Coverage(source=self.config.source, omit=self.config.omit)
        cov.start()
        self.map_test(test_name)
        cov.stop()

        return cov.get_data()

    def record_affected_files(self, coverage_data, test_name):
        line_counts = coverage_data.line_counts(fullpath=True).items()

        for filename, lines_counted in line_counts:
            if lines_counted == 0:
                self.source_map.touch(filename)

            line_nums = coverage_data.lines(filename)
            self.source_map[filename] = (test_name, line_nums)

    @property
    def untested_files(self):
        return self.source_map.untested_files

    @property
    def files(self):
        return self.source_map.files

    def match_tests_to_source(self, tests):
        test_index = 1
        num_tests = len(tests)

        for test_name in tests:
            coverage_data = self.run_coverage(test_name)

            if self.verbosity < 2:
                sys.stdout.write(spinner.next())
                sys.stdout.flush()

            self.record_affected_files(coverage_data, test_name)

            if self.verbosity >= 2:
                output_message = '[{test_index}/{total}] {test_name}\n'

                output_message = output_message.format(
                    test_index=test_index,
                    total=num_tests,
                    test_name=test_name
                )

                sys.stdout.write(output_message)
            else:
                sys.stdout.write('\b')

            test_index += 1

    def write_to_file(self, filename='.codemonmap'):
        if self.verbosity >= 2:
            sys.stdout.write('[CODEMON] Saving influence map to file {}\n\n'.format(filename))

        with open(filename, 'wb') as f:
            f.write(msgpack.packb(self.source_map.serialize(), use_bin_type=True))

    def run(self):
        if self.use_cached:
            return self.files

        self.setup()

        if self.verbosity >= 2:
            sys.stdout.write('[CODEMON] Indexing tests...\n\n')

        tests = self.tests

        if len(tests) == 0:
            error_message = ('No tests to run! Either `map_test` not '
                             'implemented or an error in specifying '
                             '`omit_tests` in config!')
            raise Exception(error_message)
        else:
            self.match_tests_to_source(tests)
            self.cleanup()
            self.write_to_file()

        return self.files


class Codemon(object):
    """Codemon

    Maps the relationship between source files and tests and runs affected
    tests when a source file changes.
    """

    def __init__(self, config=None, mapper_class=None, map_only=False,
                 verbosity=1):
        assert issubclass(mapper_class, InfluenceMapper)

        self.config = config or ConfigParser().config
        self.mapper = mapper_class(config=self.config,
                                   verbosity=verbosity)
        self.map_only = map_only
        self.verbosity = verbosity
        self.watcher = None

    def run(self):
        self.mapper.run()

        if self.map_only:
            return

        self.watcher = Watcher(self.mapper.files,
                               verbosity=self.verbosity,
                               callback=self.mapper.run_affected_tests)
        self.watcher.start()
