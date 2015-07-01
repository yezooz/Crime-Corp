from crims.engine.engine import Engine
from crims.common.models import DummyRequest

TEST_UID = 1


class TestCityUnits(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(DummyRequest(TEST_UID))

    def tearDown(self):
        pass

    def testMoveUnits1(self):
        post = {

        }

        self.assertTrue(self.engine.city.id)
        self.assertTrue(self.engine.city.move_units(post))
