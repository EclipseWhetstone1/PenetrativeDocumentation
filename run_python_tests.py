import unittest

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    # Collect tests from client and server
    suite.addTests(loader.discover("client", pattern="test_*.py"))
    suite.addTests(loader.discover("server", pattern="test_*.py"))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)