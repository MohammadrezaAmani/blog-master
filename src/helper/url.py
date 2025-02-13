def parse_route(route: list = None):
    """
    Data format must be like:
    ```python
        [router, prefix: str, tags: list[str], kwarges:dict]
    ```
    """
    if not route or len(route) == 0:
        return {}
    fixed_route = (
        route[0],
        route[1] if len(route) >= 2 else "",
        route[2] if len(route) >= 3 else None,
        route[3] if len(route) >= 4 else {},
    )
    return {
        "router": fixed_route[0],
        "prefix": fixed_route[1],
        "tags": fixed_route[2],
        **{key: value for key, value in fixed_route[3].items()},
    }


def remove_duplicates(urls_patterns: list[list]):
    result = []
    for i in urls_patterns:
        if i not in result:
            result.append(i)
    return result


def add_patterns(router, url_patterns: list[list]):
    for route in remove_duplicates(url_patterns):
        router.include_router(**parse_route(route))
    return router
