import unittest
import test_primitives, test_astypes

def get_suite():
    primitives = unittest.TestLoader().loadTestsFromModule(test_primitives)
    astypes = unittest.TestLoader().loadTestsFromModule(test_astypes)
    return unittest.TestSuite([primitives, astypes])

def main():
    unittest.TextTestRunner(verbosity=2).run(get_suite())

if __name__ == "__main__":
    main()
