import unittest
from pymongo import MongoClient
from tests.resource import *


# Empty post collection before running tests, in case the last test run
# didn't complete.
MongoClient().unittest_monkful.post.remove()

if __name__ == '__main__':
    unittest.main()