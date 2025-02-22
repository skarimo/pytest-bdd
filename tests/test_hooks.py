import textwrap


def test_hooks(pytester):
    pytester.makeconftest("")

    subdir = pytester.mkpydir("subdir")
    subdir.joinpath("conftest.py").write_text(
        textwrap.dedent(
            r"""
        def pytest_pyfunc_call(pyfuncitem):
            print('\npytest_pyfunc_call hook')

        def pytest_generate_tests(metafunc):
            print('\npytest_generate_tests hook')
    """
        )
    )

    subdir.joinpath("test_foo.py").write_text(
        textwrap.dedent(
            r"""
        from pytest_bdd import scenario

        @scenario('foo.feature', 'Some scenario')
        def test_foo():
            pass
    """
        )
    )

    subdir.joinpath("foo.feature").write_text(
        textwrap.dedent(
            r"""
        Feature: The feature
            Scenario: Some scenario
    """
        )
    )

    result = pytester.runpytest("-s")

    assert result.stdout.lines.count("pytest_pyfunc_call hook") == 1
    assert result.stdout.lines.count("pytest_generate_tests hook") == 1


def test_item_collection_does_not_break_on_non_function_items(pytester):
    """Regression test for https://github.com/pytest-dev/pytest-bdd/issues/317"""
    pytester.makeconftest(
        """
    import pytest

    @pytest.mark.tryfirst
    def pytest_collection_modifyitems(session, config, items):
        try:
            item_creator = CustomItem.from_parent  # Only available in pytest >= 5.4.0
        except AttributeError:
            item_creator = CustomItem

        items[:] = [item_creator(name=item.name, parent=item.parent) for item in items]

    class CustomItem(pytest.Item):
        def runtest(self):
            assert True
    """
    )

    pytester.makepyfile(
        """
    def test_convert_me_to_custom_item_and_assert_true():
        assert False
    """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
