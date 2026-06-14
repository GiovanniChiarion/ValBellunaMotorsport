FEATURE_FLAGS: dict[str, dict[str, list[str]]] = {
    "calendar_filters": {
        "beta": ["superadmin"],
        "stable": [],
    },
}


def feature_enabled(feature: str, ruolo: str | None) -> bool:
    if not ruolo:
        return False
    flags = FEATURE_FLAGS.get(feature, {})
    return ruolo in flags.get("beta", []) or ruolo in flags.get("stable", [])
