import unittest
from principle_alignment.play import hello

class TestMain(unittest.TestCase):

    def test_some_function(self):
        self.assertEqual(hello(), "Hello, World!")

if __name__ == '__main__':
    unittest.main()