from uuid import uuid4
import pendulum
import pytest
from prefect.orion.schemas import filters


def test_filters_must_provide_at_least_one_operator():
    class MyNewFilter(filters.PrefectFilterBaseModel):
        foo_: int = None
        bar_: int = None

    with pytest.raises(
        ValueError,
        match="Prefect Filter must have at least one operator with arguments",
    ):
        MyNewFilter()
    # should not raise
    MyNewFilter(foo_=1)
    MyNewFilter(bar_=1)
    MyNewFilter(foo_=1, bar_=1)


@pytest.mark.parametrize(
    "Filter",
    [filters.FlowFilterTags, filters.FlowRunFilterTags, filters.TaskRunFilterTags],
)
def test_all_and_is_null__filter_validation_does_not_allow_all_and_is_null(Filter):
    with pytest.raises(
        ValueError,
        match=f"Cannot provide Prefect Filter {Filter.__name__!r} all_ with is_null_ = True",
    ):
        Filter(all_=["foo"], is_null_=True)


@pytest.mark.parametrize(
    "Filter",
    [filters.FlowRunFilterDeploymentIds, filters.FlowRunFilterParentTaskRunIds],
)
def test_any_and_is_null_filter_validation_does_not_allow_any_and_is_null(Filter):
    with pytest.raises(
        ValueError,
        match=f"Cannot provide Prefect Filter {Filter.__name__!r} any_ with is_null_ = True",
    ):
        Filter(any_=[uuid4()], is_null_=True)


@pytest.mark.parametrize(
    "Filter",
    [
        filters.FlowRunFilterStartTime,
        filters.TaskRunFilterStartTime,
        filters.FlowRunFilterNextScheduledStartTime,
        filters.FlowRunFilterExpectedStartTime,
    ],
)
def test_time_filters_before_must_be_greater_than_after(Filter):
    with pytest.raises(
        ValueError,
        match=f"Cannot provide Prefect Filter {Filter.__name__!r} where before_ is less than after_",
    ):
        Filter(before_=pendulum.now("UTC"), after_=pendulum.now("UTC").add(days=1))
