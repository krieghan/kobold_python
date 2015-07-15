import unittest

from kobold import swap, doubles

class Host(object):
    def subject(self, arg, kwarg=None):
        return "original subject"


class TestSwap(unittest.TestCase):
    def setUp(self):
        self.safe_swap = swap.SafeSwap()

    def tearDown(self):
        self.safe_swap.rollback()

    def test_swap_and_rollback(self):
        stub_function = doubles.StubFunction(returns=1)
        self.safe_swap.swap(
                Host,
                'subject',
                stub_function)
        host = Host()
        self.assertEqual(1, host.subject(1, kwarg=2))
        
        self.safe_swap.rollback()

        self.assertEqual('original subject', host.subject(arg=1, kwarg=1))

        


