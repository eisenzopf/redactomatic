import redact
import unittest

class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

class TestCardinal(unittest.TestCase):
    def test_cardinal(self):
        # ['[CARDINAL]','[CARDINAL]','[CARDINAL]','[CARDINAL]','[CARDINAL]','[CARDINAL]']
        matches = [
            ["ONE","TWO","THREE", "FOUR", "FIVE", "SIX"]
        ]
        
        for match in matches:
            occurances = ['[CARDINAL]' for x in range(len(match))]
            self.assertEqual(redact.cardinal(match), occurances)


if __name__ == '__main__':
    unittest.main()