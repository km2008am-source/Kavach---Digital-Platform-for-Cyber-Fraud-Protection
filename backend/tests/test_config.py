"""HASH_SALT guard: a weak salt must stop the app in demo/prod and warn in dev."""
import pytest
from pydantic import ValidationError

from kavach.analysis import pulse
from kavach.analysis.settings import DEFAULT_SALT, Settings, salt_is_weak

STRONG = "9f2c4e7a1b8d3f60c5e2a9b7d4f1c8e3"          # test-only value, not a real secret


@pytest.mark.parametrize("env", ["demo", "prod"])
@pytest.mark.parametrize("salt", [DEFAULT_SALT, "", "short-salt", "  change-me  "])
def test_weak_salt_refused_in_demo_and_prod(env, salt):
    with pytest.raises(ValidationError, match="HASH_SALT"):
        Settings(_env_file=None, APP_ENV=env, HASH_SALT=salt)


def test_strong_salt_accepted_in_prod():
    assert Settings(_env_file=None, APP_ENV="prod", HASH_SALT=STRONG).HASH_SALT == STRONG


@pytest.mark.parametrize("env", ["dev", "test"])
def test_default_salt_allowed_for_local_work(env):
    assert Settings(_env_file=None, APP_ENV=env).HASH_SALT == DEFAULT_SALT


def test_salt_is_weak():
    assert salt_is_weak(DEFAULT_SALT) and salt_is_weak("x" * 15)
    assert not salt_is_weak(STRONG)


def test_reporter_key_warns_once_with_weak_salt(monkeypatch):
    monkeypatch.setattr(pulse.settings, "HASH_SALT", DEFAULT_SALT)
    monkeypatch.setattr(pulse, "_weak_salt_warned", False)
    with pytest.warns(RuntimeWarning, match="HASH_SALT"):
        pulse.reporter_key("wa-1")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")             # a second warning would raise here
        pulse.reporter_key("wa-2")


def test_reporter_key_silent_with_strong_salt(monkeypatch):
    monkeypatch.setattr(pulse.settings, "HASH_SALT", STRONG)
    monkeypatch.setattr(pulse, "_weak_salt_warned", False)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pulse.reporter_key("wa-1")


@pytest.mark.parametrize("raw, normalised", [("development", "dev"), ("Production", "prod"), ("testing", "test")])
def test_person1_app_env_names_are_understood(raw, normalised):
    assert Settings(_env_file=None, APP_ENV=raw, HASH_SALT=STRONG).APP_ENV == normalised


def test_unknown_app_env_is_treated_as_strict():
    with pytest.raises(ValidationError, match="HASH_SALT"):
        Settings(_env_file=None, APP_ENV="staging-2", HASH_SALT=DEFAULT_SALT)
