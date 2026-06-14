from app.features import feature_enabled


def test_feature_enabled_for_superadmin():
    assert feature_enabled("calendar_filters", "superadmin") is True


def test_feature_enabled_for_admin():
    assert feature_enabled("calendar_filters", "admin") is False


def test_feature_enabled_for_membro():
    assert feature_enabled("calendar_filters", "membro") is False


def test_feature_enabled_none_role():
    assert feature_enabled("calendar_filters", None) is False


def test_feature_enabled_unknown_feature():
    assert feature_enabled("nonexistent", "superadmin") is False


def test_feature_enabled_unknown_role():
    assert feature_enabled("calendar_filters", "hacker") is False
