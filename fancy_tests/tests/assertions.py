"""
Stand-ins for nose.tools.eq_ and ok_, which the tests were written with.
nose cannot be imported on Python 3.12+.
"""


def eq_(first, second, message=None):
    assert first == second, message or "%r != %r" % (first, second)


def ok_(expression, message=None):
    assert expression, message
