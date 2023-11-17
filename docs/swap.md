# Swap

Swapping is replacing the value of an attribute at run-time.  Under certain circumstances, you could call it "monkey-patching".  In an automated test, some might call it "mocking" or "stubbing".  Basically, though, it's just assignment, with one crucial difference: when I talk about "swapping", I imply that we might want to undo the swap later on - to return everything back the way it was.

## Basic swapping

### How do I swap an attribute with kobold?

Let's say you have a settings module, and a setting called "TRIES" that's an attribute on that module:

```python
TRIES = 1
```

TRIES has a value of 1, but you want to make the value 3

You want to call swap with 3 arguments - the object in question (everything in python is an object, so this could be a class or a module, like in this case), the name of the attribute (a string), and the new value.  You do this like so:

```python
from kobold import swap

import settings

swapper = swap.SafeSwap()
swapper.swap(
    settings,
    'TRIES'
    3)

#  This will print 3
print(settings.TRIES)
```

### How do I put everything back when I'm done?

You've had your fun, and you want to restore TRIES back to what it was initially:

```python
swapper.rollback()

# This will print 1
print(settings.TRIES)
```

We only swapped one attribute, here, but we could have called swapper.swap to replace multiple things.  Calling rollback returns everything back the way it was.

### What if I only want to undo one assignment, not all of them?

In some circumstances, maybe you're not ready to restore everything back to the way it was when you found it, but instead only want to put back one specific assignment.  Here's how you do that:

```python
swapper.unswap(settings, 'TRIES')

# This will print 1
print(settings.TRIES)
```

### Can I swap values of a dictionary, rather than attributes of an object?

Maybe settings isn't a module, but a dictionary, like this:

```python
settings = {
    'TRIES': 1}
```

You'd do your swap like this:

```python
swapper.swap(
    settings,
    'TRIES',
    3,
    swap_type='key')

# This will print 3
print(settings['TRIES'])
```

(swap_type is "member" by default).

## Testing

Swapping is very useful in automated testing.  You might want to change a setting (like we did above) for one test case, but not have it affect other test cases.  In fact, "state leakage" between test cases is one of the worst things that can happen - it is very hard to debug, as you need to comb through the whole test suite to figure out where things went wrong.

### So, how would I swap in a test case

You can setup the swapper in the setup of your testcase, swap the setting, and then roll back all swaps in the teardown portion of your testcase.  Here's how you'd do it in xUnit:

```python
import unittest

import settings

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.swapper = swap.SafeSwap()

    def tearDown(self):
        self.swapper.rollback() 

# Both test_settings_3 and test_settings_1 will pass
class MyTestCase(BaseTestCase):
    def test_settings_3(self):
        self.swapper.swap(settings, 'TRIES', 3)
        self.assertEqual(3, settings.TRIES)

    def test_settings_1(self):
        self.assertEqual(1, settings.TRIES)
```

We've defined a BaseTestCase class which defines setUp and tearDown.  We setup the swapper in setUp, so any testcases which inherit from BaseTestCase will automatically have a swapper defined.  We also define tearDown, which runs whether the test case passes or fails.  test_settings_3 swaps the setting to 3, and asserts that it is 3.  Whether it passes or fails, the tearDown phase of the test will restore settings.TRIES to its previous value of 1.  test_settings_1 doesn't swap the setting, and asserts that the value is 1 (which it will be, assuming we're still using the settings.py module we defined above, which set TRIES to 1).  

Maybe you think all this inheritance is over-engineering.  For the sake of argument, let's look at a simpler, but more problematic example:

```python
# Both test_settings_3 and test_settings_1 will still pass, but I certainly don't approve.
class MyTestCase(unittest.TestCase):
    def test_settings_3(self):
        swapper = swap.SafeSwap()
        swapper.swap(settings, 'TRIES', 3)
        self.assertEqual(3, settings.TRIES)
        swapper.rollback()

    def test_settings_1(self):
        self.assertEqual(1, settings.TRIES)
```

There, that looks simpler.  BaseTestCase isn't involved (note that our MyTestCase class inherits from unittest's TestCase) and there are no setUps or tearDowns.  This will actually work, too.  Both of these test cases pass.  Let's make a small change, though:

```python

# Depending on the order in which these tests are run, either one or both test cases will fail
class MyTestCase(unittest.TestCase):
    def test_settings_3(self):
        swapper = swap.SafeSwap()
        swapper.swap(settings, 'TRIES', 3)
        self.assertEqual(5, settings.TRIES)
        swapper.rollback()

    def test_settings_1(self):
        self.assertEqual(1, settings.TRIES)
```

I purposefully screwed up the assertion in test_settings_3 so that it will fail.  What this means is that swapper.rollback will not be called, so the value of settings.TRIES will continue to be 3 until either it is assigned to something else, or the process dies (at the end of the test suite).  Perhaps test_settings_1 was run before test_settings_3 - if so, test_settings_1 will pass and test_settings_3 will fail.  But maybe test_settings_3 is the first test to be run - in this event, test_settings_1 will fail, as well.
    
According to xUnit, the order in which tests run is not defined - it could be random, depending on the test runner.  Our goal is that the test suite runs with the same result no matter which order the tests are run in - if not, we will have random, unexplained failures that will be difficult to debug.  In order for this style to work, you'd need to use try/finally like this:

```python
    def test_settings_3(self):
        swapper = swap.SafeSwap()
        try:
            swapper.swap(settings, 'TRIES', 3)
            self.assertEqual(5, settings.TRIES)
        finally:
            swapper.rollback()
```

We could do this, but we'd have to do it anytime we swapped anything, and any mistake could lead to state-leakage.  Let's not - it's best to rely on xUnit's mechanisms of setUp and tearDown.
