import pytest

from pytest_bdd import scenario, given, when, then
from pytest_bdd.scenario import GivenAlreadyUsed


test_steps = scenario('steps.feature', 'Executed step by step')


@given('I have a foo fixture with value "foo"')
def foo():
    return 'foo'


@given('there is a list')
def results():
    return []


@when('I append 1 to the list')
def append_1(results):
    results.append(1)


@when('I append 2 to the list')
def append_2(results):
    results.append(2)


@when('I append 3 to the list')
def append_3(results):
    results.append(3)


@then('foo should have value "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('the list should be [1, 2, 3]')
def check_results(results):
    assert results == [1, 2, 3]


test_when_first = scenario('steps.feature', 'When step can be the first')


@when('I do nothing')
def do_nothing():
    pass


@then('I make no mistakes')
def no_errors():
    assert True


test_then_after_given = scenario('steps.feature', 'Then step can follow Given step')


@given('xyz')
def xyz():
    """Used in the test_same_step_name."""
    return

test_conftest = scenario('steps.feature', 'All steps are declared in the conftest')


def test_multiple_given(request):
    """Using the same given fixture raises an error."""
    test = scenario(
        'steps.feature',
        'Using the same given fixture raises an error',
    )
    with pytest.raises(GivenAlreadyUsed):
        test(request)


def test_step_hooks(testdir):
    """When step fails."""
    testdir.makefile('.feature', test="""
    Scenario: When step has hook on failure
        Given I have a bar
        When it fails

    Scenario: When step's dependency a has failure
        Given I have a bar
        When it's dependency fails

    Scenario: When step is not found
        Given not found

    Scenario: When step validation error happens
        Given foo
        And foo
    """)
    testdir.makepyfile("""
        import pytest
        from pytest_bdd import given, when, mark

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @when('it fails')
        def when_it_fails():
            raise Exception('when fails')

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @pytest.fixture
        def dependency():
            raise Exception('dependency fails')

        @when("it's dependency fails")
        def when_dependency_fails(dependency):
            pass

        @mark.scenario('test.feature', "When step's dependency a has failure")
        def test_when_dependency_fails():
            pass

        @mark.scenario('test.feature', 'When step has hook on failure')
        def test_when_fails():
            pass

        @mark.scenario('test.feature', 'When step is not found')
        def test_when_not_found():
            pass

        @when('foo')
        def foo():
            return 'foo'

        @mark.scenario('test.feature', 'When step validation error happens')
        def test_when_step_validation_error():
            pass
    """)
    reprec = testdir.inline_run("-k test_when_fails")
    assert reprec.ret == 1

    calls = reprec.getcalls("pytest_bdd_before_step")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_after_step")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_step_error")
    assert calls[0].request

    reprec = testdir.inline_run("-k test_when_not_found")
    assert reprec.ret == 1

    calls = reprec.getcalls("pytest_bdd_step_func_lookup_error")
    assert calls[0].request

    reprec = testdir.inline_run("-k test_when_step_validation_error")
    assert reprec.ret == 1

    reprec = testdir.inline_run("-k test_when_dependency_fails", '-vv')
    assert reprec.ret == 1

    calls = reprec.getcalls("pytest_bdd_before_step")
    assert len(calls) == 1

    calls = reprec.getcalls("pytest_bdd_step_error")
    assert calls[0].request


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makefile('.feature', test="""
    Scenario: When step has failure
        Given I have a bar
        When it fails

    Scenario: When step is not found
        Given not found

    Scenario: When step validation error happens
        Given foo
        And foo
    """)
    testdir.makepyfile("""
        import pytest
        from pytest_bdd import given, when, scenario, mark

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @when('it fails')
        def when_it_fails():
            raise Exception('when fails')

        test_when_fails_inline = scenario('test.feature', 'When step has failure')

        @mark.scenario('test.feature', 'When step has failure')
        def test_when_fails_decorated():
            pass

        test_when_not_found = scenario('test.feature', 'When step is not found')

        @when('foo')
        def foo():
            return 'foo'

        test_when_step_validation_error = scenario('test.feature', 'When step validation error happens')
    """)
    result = testdir.runpytest('-k test_when_fails_inline', '-vv')
    assert result.ret == 1
    result.stdout.fnmatch_lines('test_step_trace.py:*: test_when_fails_inline FAILED')
    assert 'INTERNALERROR' not in result.stdout.str()

    result = testdir.runpytest('-k test_when_fails_decorated', '-vv')
    assert result.ret == 1
    result.stdout.fnmatch_lines('test_step_trace.py:*: test_when_fails_decorated FAILED')
    assert 'INTERNALERROR' not in result.stdout.str()

    result = testdir.runpytest('-k test_when_not_found', '-vv')
    assert result.ret == 1
    result.stdout.fnmatch_lines('test_step_trace.py:*: test_when_not_found FAILED')
    assert 'INTERNALERROR' not in result.stdout.str()

    result = testdir.runpytest('-k test_when_step_validation_error', '-vv')
    assert result.ret == 1
    result.stdout.fnmatch_lines('test_step_trace.py:*: test_when_step_validation_error FAILED')
    assert 'INTERNALERROR' not in result.stdout.str()
