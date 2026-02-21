def ljust(value: str, width: int) -> str:
    return value.ljust(width)


def register_filters(environment):
    environment.filters["ljust"] = ljust
