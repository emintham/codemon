from unittest import TestCase

import re

from codemon.config import Config


class TestConfig(TestCase):
    def setUp(self):
        self.omit = ['*/migrations/*', '*/tests/*', '*tests.py']
        self.source = ['*/codemon/*']
        self.omit_tests = ['foo*']
        self.config = Config(omit=self.omit,
                             source=self.source,
                             omit_tests=self.omit_tests)

    def check_regex(self, regex):
        self.assertTrue(re.search(regex, 'foo'))
        self.assertTrue(re.search(regex, 'foobar'))
        self.assertFalse(re.search(regex, 'barfoo'))
        self.assertFalse(re.search(regex, 'bar'))

    def assert_config_correct(self, config):
        self.assertEqual(config.omit, self.omit)
        self.assertEqual(config.source, self.source)
        self.assertEqual(len(config.omit_tests), len(self.omit_tests))
        self.check_regex(config.omit_tests[0])

    def test_init(self):
        self.assert_config_correct(self.config)

    def test_from_file(self):
        config = Config.from_file('tests/sample_config.txt')
        self.assert_config_correct(config)
