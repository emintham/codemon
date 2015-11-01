from collections import defaultdict


__all__ = ['SourceMap']


class _SourceTestMap(object):
    """_SourceTestMap

    defaultdict(set) where:
        key:    line number
        value:  set of tests affected by the line
    """

    def __init__(self, filename=None, other=None):
        assert filename or other

        if filename:
            self.filename = filename
            self._dict = defaultdict(set)
        else:
            self.filename, self._dict = other

    def __getitem__(self, line_number):
        return self._dict[line_number]

    def __delitem__(self, line_number):
        del self._dict[line_number]

    def __repr__(self):
        return repr(self._dict)

    def __iter__(self):
        return iter(self._dict)

    def __eq__(self, other):
        return (self.filename == other.filename and
                self._dict == other._dict)

    @property
    def all_affected_tests(self):
        tests = self._dict.values()

        if tests:
            affected_tests = set.union(*tests)
            return list(affected_tests)
        else:
            return []

    @staticmethod
    def deserialize(serialized_data, reverse_lookup):
        assert isinstance(serialized_data, tuple)
        assert len(serialized_data) == 2
        assert isinstance(serialized_data[1], dict)

        d = {}

        for line_num, test_names in serialized_data[1].items():
            d[line_num] = set((reverse_lookup[testname]
                               for testname in test_names))

        return _SourceTestMap(other=(serialized_data[0], d))

    @staticmethod
    def serialize(obj, testname_dict):
        d = {}

        for line_num, test_names in obj._dict.items():
            test_indices = [testname_dict[testname] for testname in test_names]
            d[line_num] = sorted(test_indices)

        return (obj.filename, d)

    @property
    def is_untested(self):
        return len(self._dict) == 0

    def add(self, line_number, test_name):
        self._dict[line_number].add(test_name)


class SourceMap(object):
    """SourceMap

    A collection of SourceTestMaps with a convenient interface.
    """

    def __init__(self, other=None):
        self._source_map = {}

        if other is not None:
            self._deserialize(other)

    def __getitem__(self, filename):
        return self._source_map[filename]

    def __setitem__(self, filename, coverage_data):
        test_name, line_nums = coverage_data

        self.touch(filename)

        for num in line_nums:
            self._source_map[filename].add(num, test_name)

    def __delitem__(self, filename):
        del self._source_map[filename]

    def __repr__(self):
        return repr(self._source_map)

    def __iter__(self):
        return iter(self._source_map)

    @property
    def files(self):
        return self._source_map.keys()

    @property
    def untested_files(self):
        return [filename
                for filename, source in self._source_map.items()
                if source.is_untested]

    def suite(self, filenames=None):
        """
        Returns a list of all related tests for a given list of source files.
        """
        filenames = filenames or self._source_map.keys()

        return [test
                for filename in filenames
                for test in self._source_map[filename].all_affected_tests]

    def _deserialize(self, other):
        reverse_testname_lookup, d = other

        for k, v in d.items():
            self._source_map[k] = _SourceTestMap.deserialize(v)

    def serialize(self):
        d = {}
        testname_lookup = {
            testname: index
            for index, testname in enumerate(self.suite())
        }

        for k, v in self._source_map.items():
            d[k] = v.serialize(testname_lookup)

        reverse_testname_lookup = {
            index: testname
            for testname, index in testname_lookup.items()
        }

        return (reverse_testname_lookup, d)

    def touch(self, filename):
        if filename not in self._source_map:
            self._source_map[filename] = _SourceTestMap(filename)
