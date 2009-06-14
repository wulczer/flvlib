import unittest
import test_primitives, test_astypes

if __name__ == "__main__":
    primitives = unittest.TestLoader().loadTestsFromModule(test_primitives)
    astypes = unittest.TestLoader().loadTestsFromModule(test_astypes)
    suite = unittest.TestSuite([primitives, astypes])
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
