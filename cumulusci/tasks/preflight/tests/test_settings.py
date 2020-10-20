from cumulusci.tasks.preflight.settings import CheckSettingsValue
from cumulusci.tasks.salesforce.tests.util import create_task

from simple_salesforce.exceptions import SalesforceMalformedRequest

import pytest
import responses


JSON_RESPONSE = {
    "records": [{"IntVal": 3, "FloatVal": 3.0, "BoolVal": True, "StringVal": "foo"}],
    "done": True,
    "totalSize": 1,
}


@responses.activate
@pytest.mark.parametrize(
    "settings_field,value,outcome",
    [
        ("IntVal", 3, True),
        ("FloatVal", 3.0, True),
        ("BoolVal", "true", True),
        ("StringVal", "foo", True),
        ("StringVal", "bad", False),
    ],
)
def test_check_settings(settings_field, value, outcome):
    responses.add(
        "GET",
        f"https://test.salesforce.com/services/data/v50.0/tooling/query/?q=SELECT+{settings_field}+FROM+ChatterSettings",
        json=JSON_RESPONSE,
    )
    task = create_task(
        CheckSettingsValue,
        {
            "settings_type": "ChatterSettings",
            "settings_field": settings_field,
            "value": value,
        },
    )

    task()

    assert task.return_values is outcome


@responses.activate
def test_check_settings__no_settings():
    responses.add(
        "GET",
        "https://test.salesforce.com/services/data/v50.0/tooling/query/?q=SELECT+Foo+FROM+ChatterSettings",
        json={"records": []},
    )
    task = create_task(
        CheckSettingsValue,
        {
            "settings_type": "ChatterSettings",
            "settings_field": "Foo",
            "value": True,
        },
    )

    task()

    assert task.return_values is False


@responses.activate
def test_check_settings__failure():
    responses.add(
        "GET",
        status=400,
        url="https://test.salesforce.com/services/data/v50.0/tooling/query/?q=SELECT+Test+FROM+NoSettings",
        json={},
    )
    task = create_task(
        CheckSettingsValue,
        {
            "settings_type": "NoSettings",
            "settings_field": "Test",
            "value": True,
            "treat_missing_as_failure": True,
        },
    )

    task()

    assert task.return_values is False


@responses.activate
def test_check_settings__exception():
    responses.add(
        "GET",
        status=400,
        url="https://test.salesforce.com/services/data/v50.0/tooling/query/?q=SELECT+Test+FROM+NoSettings",
        json={},
    )
    task = create_task(
        CheckSettingsValue,
        {
            "settings_type": "NoSettings",
            "settings_field": "Test",
            "value": True,
        },
    )

    with pytest.raises(SalesforceMalformedRequest):
        task()

    assert task.return_values is False
