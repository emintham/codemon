import re

import yaml


class Config(object):
    """Configuration

    `coverage.py` is used internally to check for influence. Specify `omit` and
    `source` to include/exclude files to measure influence of. See the
    documentation of coverage.py for more information. `omit` defaults to being
    empty while `source` defaults to the current directory if not specified.

    Additionally, also specify `omit_tests` to omit a list of tests. It accepts
    `*` in each pattern optionally that matches anything. e.g. `*foobar*` will
    exclude any tests having `foobar` in its full path. `omit_tests` defaults
    to being empty if not specified.
    """

    DEFAULT_FILENAME = '.codemonrc'

    def __init__(self, omit=[], source='.', omit_tests=[]):
        self.omit = omit or []
        self.source = source or '.'
        self.omit_tests = omit_tests or []

        # initialize omit_tests regex
        self.omit_tests = [self._regex_replacement(s) for s in self.omit_tests]

    def _regex_replacement(self, pattern):
        return re.compile('^' + pattern.replace('*', '.*'))

    def is_omitted_test(self, test_name):
        return any([re.search(pattern, test_name)
                    for pattern in self.omit_tests])

    @classmethod
    def from_file(cls, filename=None):
        filename = filename or cls.DEFAULT_FILENAME

        try:
            with open(filename, 'rb') as f:
                config = yaml.load(f.read())
                return Config(**config)
        except (yaml.parser.ParserError, ValueError):
            raise Exception('Error parsing config!')
