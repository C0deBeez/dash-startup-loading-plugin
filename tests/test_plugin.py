import html
import json
import re
import sys
from importlib.resources import files
from types import SimpleNamespace

import pytest
from dash import Dash
from dash import html as dash_html

import dash_startup_loading_plugin as loading_plugin
from dash_startup_loading_plugin import (
    configure,
    configure_dac,
    configure_fac,
    configure_dmc,
    get_config,
    reset_config,
)
from dash_startup_loading_plugin.plugin import (
    _configure_installed_integrations,
    _inject_overlay,
)


@pytest.fixture(autouse=True)
def restore_defaults():
    reset_config()
    yield
    reset_config()


def _data_config(index: str) -> dict:
    match = re.search(r'data-config="([^"]+)"', index)
    assert match is not None
    return json.loads(html.unescape(match.group(1)))


def test_public_integration_helpers_use_component_library_abbreviations():
    assert hasattr(loading_plugin, "configure_dac")
    assert hasattr(loading_plugin, "configure_dmc")
    assert not hasattr(loading_plugin, "configure_antd")
    assert not hasattr(loading_plugin, "configure_mantine")


def test_injects_overlay_after_body_with_custom_attributes():
    index = '<!doctype html><html><head></head><body class="app"><main></main></body></html>'

    result = _inject_overlay(index)

    assert '<style data-dash-loading-resource="style">' in result
    assert result.index("<style") < result.index("</head>")
    assert '<script data-dash-loading-resource="theme">' in result
    assert result.index('data-dash-loading-resource="theme"') < result.index("</head>")
    assert '<body class="app"><div id="dash-loading"' in result
    assert '<script data-dash-loading-resource="script">' in result
    assert result.index('id="dash-loading"') < result.index(
        '<script data-dash-loading-resource="script">'
    )
    assert result.count(" data-dash-loading ") == 1
    assert '<span class="dash-loading__spinner"' in result
    assert _data_config(result)["requiredSelectors"] == ["#react-entry-point"]
    assert _data_config(result)["pendingSelector"] is None


def test_waiting_for_async_components_is_opt_in():
    configure(pending_selector="[data-async-placeholder]")

    result = _inject_overlay("<html><body><main></main></body></html>")

    assert _data_config(result)["pendingSelector"] == "[data-async-placeholder]"


def test_injection_is_idempotent_and_can_be_disabled():
    index = "<html><body><main></main></body></html>"
    once = _inject_overlay(index)
    assert _inject_overlay(once) == once

    configure(enabled=False)
    assert _inject_overlay(index) == index


def test_serializes_readiness_configuration_and_escapes_attributes():
    configure(
        overlay_id='loader"safe',
        aria_label='Loading "application"',
        required_selectors=["#header", "#menu"],
        pending_selector="[data-lazy-placeholder]",
        timeout_ms=None,
        minimum_display_ms=250,
        fade_duration_ms=90,
    )

    result = _inject_overlay("<html><body><main></main></body></html>")
    config = _data_config(result)

    assert 'id="loader&quot;safe"' in result
    assert 'aria-label="Loading &quot;application&quot;"' in result
    assert config == {
        "rootSelector": "#react-entry-point",
        "requiredSelectors": ["#header", "#menu"],
        "pendingSelector": "[data-lazy-placeholder]",
        "timeoutMs": None,
        "minimumDisplayMs": 250,
        "fadeDurationMs": 90,
    }


def test_custom_loader_html_is_intentionally_preserved():
    configure(custom_loader_html='<div class="brand-loader">Please wait</div>')

    result = _inject_overlay("<html><body></body></html>")

    assert '<div class="brand-loader">Please wait</div>' in result


def test_configuration_validation():
    with pytest.raises(TypeError, match="required_selectors"):
        configure(required_selectors="#header")
    with pytest.raises(ValueError, match="timeout_ms"):
        configure(timeout_ms=-1)
    with pytest.raises(ValueError, match="theme_mode"):
        configure(theme_mode="sepia")
    with pytest.raises(ValueError, match="dash_theme_component_id"):
        configure(dash_theme_component_id="")
    with pytest.raises(TypeError, match="Unknown"):
        configure(unknown=True)
    assert get_config().required_selectors == ("#react-entry-point",)


def test_mantine_configuration_uses_semantic_theme_defaults(monkeypatch):
    calls = []
    fake_dmc = SimpleNamespace(
        DEFAULT_THEME={
            "white": "#fff",
            "colors": {"dark": [""] * 7 + ["#242424"]},
        },
        pre_render_color_scheme=lambda: calls.append("registered"),
    )
    monkeypatch.setitem(sys.modules, "dash_mantine_components", fake_dmc)
    monkeypatch.setattr(
        "dash_startup_loading_plugin.plugin._mantine_prerender_registered",
        False,
    )

    config = configure_dmc(minimum_display_ms=200)

    assert config.background == "#fff"
    assert config.dark_background == "#242424"
    assert config.pending_selector is None
    assert config.minimum_display_ms == 200
    assert calls == ["registered"]


def test_antd_configuration_matches_library_backgrounds_and_allows_overrides():
    config = configure_dac()
    assert config.background == "#ffffff"
    assert config.dark_background == "#121212"

    config = configure_dac(background="#f5f5f5", dark_background="#202020")
    assert config.background == "#f5f5f5"
    assert config.dark_background == "#202020"


def test_installed_dash_ant_design_is_configured_automatically(monkeypatch):
    monkeypatch.setattr(
        "dash_startup_loading_plugin.plugin.find_spec",
        lambda name: object() if name == "dash_antd_components" else None,
    )

    config = _configure_installed_integrations()

    assert config.background == "#ffffff"
    assert config.dark_background == "#121212"


def test_fac_configuration_matches_antd_backgrounds_and_allows_overrides():
    config = configure_fac()
    assert config.background == "#ffffff"
    assert config.dark_background == "#121212"

    config = configure_fac(background="#fafafa", dark_background="#1f1f1f")
    assert config.background == "#fafafa"
    assert config.dark_background == "#1f1f1f"


def test_resolved_theme_controls_overlay_colors():
    css = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/loading.css")
        .read_text(encoding="utf-8")
    )

    assert 'html[data-dash-loading-theme="light"] .dash-loading' in css
    assert 'html[data-dash-loading-theme="dark"] .dash-loading' in css


def test_theme_bootstrap_supports_dash_tailwind_and_mantine_conventions():
    script = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/theme.js")
        .read_text(encoding="utf-8")
    )

    assert "_dash_persistence." in script
    assert 'classList.contains("dark")' in script
    assert 'data-mantine-color-scheme' in script
    assert 'mantine-color-scheme-value' in script
    assert 'data-dash-loading-theme' in script
    assert 'name === "system" || name === "auto"' in script


def test_theme_bootstrap_defaults_to_light_without_an_app_preference():
    script = (
        files("dash_startup_loading_plugin")
        .joinpath("resources/theme.js")
        .read_text(encoding="utf-8")
    )

    assert (
        'rootTheme() || dashPersistenceTheme() || conventionalStoredTheme() || "light"'
        in script
    )
    assert 'conventionalStoredTheme() || "system"' not in script
    assert 'theme === "system"' in script
    assert 'matchMedia("(prefers-color-scheme: dark)")' in script


def test_theme_bootstrap_serializes_component_id_and_explicit_mode():
    configure(theme_mode="dark", dash_theme_component_id="theme-provider")

    result = _inject_overlay("<html><head></head><body></body></html>")

    assert (
        'window.__dashLoadingThemeConfig={"themeMode":"dark",'
        '"dashThemeComponentId":"theme-provider"};'
    ) in result


def test_resource_names_drop_startup_and_preserve_dash_default_loading_selector():
    resources = files("dash_startup_loading_plugin").joinpath("resources")
    resource_names = {resource.name for resource in resources.iterdir() if resource.is_file()}
    resource_text = "\n".join(
        resources.joinpath(name).read_text(encoding="utf-8") for name in sorted(resource_names)
    )

    assert resource_names == {"loading.css", "loading.js", "theme.js"}
    assert "startup" not in resource_text.lower()
    assert "._dash-loading" in resource_text
    assert "window.dashLoading" in resource_text
    assert "dash-loading:ready" in resource_text


def test_dash_index_contains_overlay_and_inline_resources():
    app = Dash(__name__)
    app.layout = dash_html.Div("Ready", id="ready")

    client = app.server.test_client()
    response = client.get("/")
    index = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "data-dash-loading" in index
    assert '<style data-dash-loading-resource="style">' in index
    assert '<script data-dash-loading-resource="theme">' in index
    assert '<script data-dash-loading-resource="script">' in index
    assert "resources/loading.css" not in index
    assert "resources/loading.js" not in index
    assert '<div class="_dash-loading">' in index
