def validate_keys_strict(dictionary, allowed_keys, required_keys=None):
    """
    Validates dictionary keys against allowed and required sets.

    - No unexpected keys
    - All required keys must be present
    """

    allowed_keys = set(allowed_keys)
    required_keys = set(required_keys or [])

    dict_keys = set(dictionary.keys())

    invalid = dict_keys - allowed_keys
    missing = required_keys - dict_keys

    errors = []

    if invalid:
        errors.append(f"Invalid keys: {invalid}")

    if missing:
        errors.append(f"Missing required keys: {missing}")

    if errors:
        raise KeyError(" | ".join(errors))

