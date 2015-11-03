from collections import defaultdict, OrderedDict

import sys

import msgpack


__all__ = ['SourceMap']


class _SourceTestMap(defaultdict):
    """_SourceTestMap

    defaultdict(set) where:
        key:    line number
        value:  set of tests affected by the line
    """

    def __init__(self, filename=None):
        super(_SourceTestMap, self).__init__(set)
        self.filename = filename

    def __eq__(self, other):
        return (self.filename == other.filename and
                super(_SourceTestMap, self).__eq__(dict(other)))

    @property
    def all_affected_tests(self):
        tests = self.values()

        if tests:
            affected_tests = set.union(*tests)
            return list(affected_tests)
        else:
            return []

    @classmethod
    def deserialize(cls, serialized_data):
        ((filename, d), reverse_lookup) = serialized_data

        new_obj = cls(filename=filename)

        for line_num, test_names in d.items():
            new_obj[line_num] = set(reverse_lookup[testname]
                                    for testname in test_names)

        return new_obj

    @classmethod
    def serialize(cls, instance, testname_dict):
        assert isinstance(instance, cls)

        d = {}

        for line_num, test_names in instance.items():
            test_indices = [testname_dict[testname] for testname in test_names]
            d[line_num] = sorted(test_indices)

        return (instance.filename, d)

    @property
    def is_untested(self):
        return len(self) == 0

    def add(self, line_number, test_name):
        self[line_number].add(test_name)


class SourceMap(OrderedDict):
    """SourceMap

    An OrderedDict of SourceTestMaps with a convenient interface.
    """

    DEFAULT_FILENAME = '.codemonmap'

    def __setitem__(self, filename, coverage_data):
        if not isinstance(coverage_data, tuple):
            super(SourceMap, self).__setitem__(filename, coverage_data)
            return

        test_name, line_nums = coverage_data

        self.touch(filename)

        for num in line_nums:
            self[filename].add(num, test_name)

    @property
    def files(self):
        return self.keys()

    @property
    def untested_files(self):
        return [filename
                for filename, source in self.items()
                if source.is_untested]

    def suite(self, filenames=None):
        """
        Returns a list of all related tests for a given list of source files.
        """
        filenames = filenames or self.files

        return [test
                for filename in filenames
                for test in self[filename].all_affected_tests]

    @property
    def index(self):
        return {
            testname: index
            for index, testname in enumerate(self.suite())
        }

    @property
    def reverse_index(self):
        return dict(enumerate(self.suite()))

    @classmethod
    def deserialize(cls, serialized_data):
        data, reverse_index = serialized_data

        new_obj = cls()

        for serialized_stm in data:
            filename, _ = serialized_stm

            new_obj[filename] = _SourceTestMap.deserialize(
                (serialized_stm, reverse_index)
            )

        return new_obj

    @classmethod
    def serialize(cls, instance):
        assert isinstance(instance, cls)

        testname_lookup = instance.index.copy()

        serialized_data = []
        for filename, stm in instance.items():
            serialized_data.append(
                _SourceTestMap.serialize(stm, testname_lookup)
            )

        return (serialized_data, instance.reverse_index)

    def touch(self, filename):
        if filename not in self:
            self[filename] = _SourceTestMap(filename)

    @classmethod
    def write_to_file(cls, instance, filename=None):
        filename = filename or cls.DEFAULT_FILENAME

        output = '[CODEMON] Saving influence map to file {}\n\n'
        sys.stdout.write(output.format(filename))

        with open(filename, 'wb') as f:
            f.write(msgpack.packb(cls.serialize(instance),
                                  use_bin_type=True))

    @classmethod
    def read_from_file(cls, filename=None):
        filename = filename or cls.DEFAULT_FILENAME

        try:
            with open(filename, 'rb') as f:
                source_map = msgpack.unpackb(f.read())

            return cls.deserialize(source_map)
        except (IOError, EOFError):
            return cls()
