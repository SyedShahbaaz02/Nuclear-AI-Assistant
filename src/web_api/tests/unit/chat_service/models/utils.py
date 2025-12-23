import pytest
import json
from pydantic.fields import FieldInfo


def assert_missing_required_fields_raises(model_cls, valid_data: dict):
    """Checks that missing required fields raise ValueError during model validation.

    Args:
        model_cls (type): The model class to validate.
        valid_data (dict): A dictionary of valid model data.

    Raises:
        AssertionError: If ValueError is not raised when a required field is missing.
    """
    fields: dict[str, FieldInfo] = model_cls.model_fields
    for name, info in fields.items():
        if info.is_required():
            invalid_data = valid_data.copy()
            del invalid_data[name]
            try:
                model_cls.model_validate_json(json.dumps(invalid_data))
                pytest.fail(f"Expected ValueError when '{name}' is missing, but no exception was raised.")
            except ValueError:
                pass
