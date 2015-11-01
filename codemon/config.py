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

    def __init__(self, omit=[], source='.', omit_tests=[], config=None):
        self.omit = omit or []
        self.source = source or '.'
        self.omit_tests = omit_tests or []

        if config is not None:
            assert isinstance(config, dict)

            self.omit = config.get('omit', self.omit)
            self.source = config.get('source', self.source)
            self.omit_tests = config.get('omit_tests', self.omit_tests)

        # initialize omit_tests regex
        self.omit_tests = [self.get_regex(s) for s in self.omit_tests]

    def get_regex(self, pattern):
        return re.compile(pattern.replace('*', '.*'))

    def is_omitted_test(self, test_name):
        return any([re.search(pattern, test_name)
                    for pattern in self.omit_tests])


class ConfigParser(object):
    """Configuration

    `.codemonrc` is checked within the current directory of where
    InfluenceMapper is run to get configurations.
    """

    DEFAULT_FILENAME = '.codemonrc'

    def __init__(self, filename=None):
        self.filename = filename or self.DEFAULT_FILENAME
        self._config = None
        self._read_config()

    def _read_config(self):
        try:
            with open(self.filename, 'rb') as f:
                config = yaml.load(f.read())
                self._config = Config(config=config)
        except (yaml.parser.ParserError, ValueError):
            raise Exception('Error parsing config!')

    @property
    def config(self):
        return self._config
