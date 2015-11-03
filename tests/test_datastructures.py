from unittest import TestCase

from codemon.datastructures import _SourceTestMap, SourceMap


class Test_SourceTestMap(TestCase):
    def setUp(self):
        self.filename = 'foo.py'
        self.obj = _SourceTestMap(filename=self.filename)

        self.lookup = {
            'test_foo': 0,
            'test_bar': 1,
            'test_foo_again': 2
        }

        self.reverse_lookup = {
            0: 'test_foo',
            1: 'test_bar',
            2: 'test_foo_again'
        }

        self.obj[1].add('test_foo')
        self.obj[1].add('test_bar')
        self.obj[5].add('test_foo_again')

        self.expected_dict = {
            1: [0, 1],
            5: [2]
        }
        self.expected_serialized_data = (self.filename, self.expected_dict)

    def test_eq(self):
        other_obj = _SourceTestMap(filename=self.filename)

        other_obj[1].add('test_bar')
        other_obj[5].add('test_foo_again')
        other_obj[1].add('test_foo')

        self.assertEqual(other_obj, self.obj)

    def test_getitem(self):
        expected = set(['test_foo', 'test_bar'])
        self.assertEqual(self.obj[1], expected)

    def test_untested_file(self):
        other_obj = _SourceTestMap('bar.py')
        self.assertTrue(other_obj.is_untested)

    def test_serialize(self):
        self.assertEqual(_SourceTestMap.serialize(self.obj, self.lookup),
                         self.expected_serialized_data)

    def test_deserialize(self):
        actual = _SourceTestMap.deserialize((self.expected_serialized_data,
                                             self.reverse_lookup))
        self.assertEqual(actual, self.obj)

    def test_serialize_deserialize_are_inverses(self):
        serialized = _SourceTestMap.serialize(self.obj, self.lookup)
        actual = _SourceTestMap.deserialize((serialized,
                                             self.reverse_lookup))

        self.assertEqual(actual, self.obj)


class TestSourceMap(TestCase):
    def setUp(self):
        self.obj = SourceMap()
        self.filenames = ['foo.py', 'bar.py']
        self.tests = ['test_foo', 'test_foo_again', 'test_bar']
        self.covered_lines = [1, 3, 5]
        self.coverage_data = (self.tests[2], self.covered_lines)

        self.obj.touch(self.filenames[0])
        self.obj[self.filenames[1]] = self.coverage_data

        self.expected_reverse_index = self.obj.reverse_index.copy()
        self.expected_index = self.obj.index.copy()
        test_bar_index = self.expected_index['test_bar']

        self.expected_serialized_data = [
            ('foo.py', {}),
            ('bar.py', {
                1: [test_bar_index],
                3: [test_bar_index],
                5: [test_bar_index],
            })
        ]

    def test_touch(self):
        other_obj = SourceMap()
        self.assertEqual(len(other_obj), 0)

        other_file = 'other_file.py'
        other_obj.touch(other_file)
        self.assertEqual(len(other_obj), 1)
        self.assertEqual(other_obj[other_file], _SourceTestMap(other_file))

    def test_getitem(self):
        expected = _SourceTestMap(self.filenames[1])
        for line_num in self.covered_lines:
            expected.add(line_num, self.tests[2])

        self.assertEqual(self.obj[self.filenames[1]], expected)

    def test_contains(self):
        self.assertTrue(self.filenames[0] in self.obj)
        self.assertTrue(self.filenames[1] in self.obj)

    def test_get(self):
        self.assertEqual(self.obj.get(self.filenames[0]),
                         _SourceTestMap(self.filenames[0]))

        self.assertIsNone(self.obj.get('no_such_file.py', None))

    def test_delitem(self):
        del self.obj[self.filenames[1]]

        with self.assertRaises(KeyError):
            self.obj[self.filenames[1]].files

    def test_untested_files_property(self):
        self.assertEqual(self.obj.untested_files, [self.filenames[0]])

    def test_files_property(self):
        self.assertEqual(self.obj.files, self.filenames)

    def test_suite(self):
        self.assertEqual(self.obj.suite(), [self.tests[2]])

        self.obj[self.filenames[0]] = (self.tests[0], [1, 2])
        self.obj[self.filenames[0]] = (self.tests[1], [3, 4])

        self.assertEqual(self.obj.suite(), self.tests)
        self.assertEqual(self.obj.suite([self.filenames[0]]), self.tests[:-1])
        self.assertEqual(self.obj.suite([self.filenames[1]]), self.tests[-1:])

    def test_serialize(self):
        serialized_data = SourceMap.serialize(self.obj)

        self.assertEqual(serialized_data[0],
                         self.expected_serialized_data)
        self.assertEqual(serialized_data[1], self.obj.reverse_index)

    def test_deserialize(self):
        actual = SourceMap.deserialize((self.expected_serialized_data,
                                        self.obj.reverse_index))
        self.assertEqual(actual, self.obj)

    def test_serialize_deserialize_are_inverses(self):
        serialized = SourceMap.serialize(self.obj)
        actual = SourceMap.deserialize(serialized)

        self.assertEqual(actual, self.obj)

    def test_file_operations_save_state(self):
        SourceMap.write_to_file(self.obj)
        retrieved_obj = SourceMap.read_from_file()

        self.assertEqual(self.obj, retrieved_obj)
