import unittest
import test_primitives, test_astypes, test_helpers

def get_suite():
    modules = (test_primitives, test_astypes, test_helpers)
    suites = [unittest.TestLoader().loadTestsFromModule(module) for
              module in modules]
    return unittest.TestSuite(suites)

def main():
    unittest.TextTestRunner(verbosity=2).run(get_suite())

if __name__ == "__main__":
    main()
