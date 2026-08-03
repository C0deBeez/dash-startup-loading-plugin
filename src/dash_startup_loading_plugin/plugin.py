"""Dash Hooks registration and startup-overlay configuration."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, replace
from functools import lru_cache
from html import escape
from importlib.resources import files
from importlib.util import find_spec
from threading import RLock
from typing import Any

from dash import hooks

_OVERLAY_MARKER = "data-dash-loading"
_BODY_PATTERN = re.compile(r"<body(?:\s[^>]*)?>", flags=re.IGNORECASE)
_HEAD_END_PATTERN = re.compile(r"</head\s*>", flags=re.IGNORECASE)
_CONFIG_LOCK = RLock()
_ANTD_LIGHT_BACKGROUND = "#ffffff"
_ANTD_DARK_BACKGROUND = "#121212"
_mantine_prerender_registered = False


@dataclass(frozen=True)
class StartupLoadingConfig:
    """Configuration serialized into the startup overlay.

    ``custom_loader_html`` is inserted verbatim and must only contain trusted
    HTML supplied by the application author.
    """

    enabled: bool = True
    overlay_id: str = "dash-loading"
    aria_label: str = "Loading"
    root_selector: str = "#react-entry-point"
    required_selectors: tuple[str, ...] = ("#react-entry-point",)
    pending_selector: str | None = None
    timeout_ms: int | None = 6000
    minimum_display_ms: int = 0
    fade_duration_ms: int = 160
    z_index: int = 9999
    background: str = "#ffffff"
    dark_background: str = "#0f0f0f"
    color: str = "#1677ff"
    dark_color: str = "#4096ff"
    theme_mode: str = "auto"
    dash_theme_component_id: str | None = None
    spinner_size_px: int = 28
    spinner_stroke_px: int = 3
    hide_default_loading: bool = True
    custom_loader_html: str | None = None


_DEFAULT_CONFIG = StartupLoadingConfig()
_config = _DEFAULT_CONFIG


def _selector_tuple(value: Iterable[str] | str) -> tuple[str, ...]:
    if isinstance(value, str):
        raise TypeError("required_selectors must be an iterable of CSS selector strings")
    selectors = tuple(value)
    if not all(isinstance(selector, str) and selector.strip() for selector in selectors):
        raise ValueError("required_selectors must contain non-empty CSS selector strings")
    return selectors


def _validate(config: StartupLoadingConfig) -> StartupLoadingConfig:
    if not isinstance(config.enabled, bool):
        raise TypeError("enabled must be a boolean")
    if not isinstance(config.overlay_id, str) or not config.overlay_id.strip():
        raise ValueError("overlay_id must be a non-empty string")
    if not isinstance(config.root_selector, str) or not config.root_selector.strip():
        raise ValueError("root_selector must be a non-empty CSS selector")
    if config.pending_selector is not None and (
        not isinstance(config.pending_selector, str) or not config.pending_selector.strip()
    ):
        raise ValueError("pending_selector must be None or a non-empty CSS selector")
    if config.timeout_ms is not None and config.timeout_ms < 0:
        raise ValueError("timeout_ms must be None or greater than or equal to zero")
    if config.theme_mode not in {"auto", "light", "dark"}:
        raise ValueError("theme_mode must be 'auto', 'light', or 'dark'")
    if config.dash_theme_component_id is not None and (
        not isinstance(config.dash_theme_component_id, str) or not config.dash_theme_component_id.strip()
    ):
        raise ValueError("dash_theme_component_id must be None or a non-empty string")
    for name in ("minimum_display_ms", "fade_duration_ms", "spinner_size_px", "spinner_stroke_px"):
        if getattr(config, name) < 0:
            raise ValueError(f"{name} must be greater than or equal to zero")
    return config


def configure(**changes: Any) -> StartupLoadingConfig:
    """Update the process-wide plugin configuration.

    Call this before creating ``dash.Dash``. The Dash hooks registry is
    process-wide, so one configuration is shared by all apps in the process.
    """

    valid_names = {field.name for field in fields(StartupLoadingConfig)}
    unknown = set(changes).difference(valid_names)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise TypeError(f"Unknown startup loading option(s): {names}")
    if "required_selectors" in changes:
        changes["required_selectors"] = _selector_tuple(changes["required_selectors"])

    global _config
    with _CONFIG_LOCK:
        _config = _validate(replace(_config, **changes))
        return _config


def configure_dmc(**changes: Any) -> StartupLoadingConfig:
    """Configure seamless startup colors for Dash Mantine Components.

    Dash Mantine Components remains an optional dependency. This helper reads
    its active default theme and registers its pre-render color-scheme hook.
    Explicit keyword arguments override all integration defaults.
    """

    try:
        import dash_mantine_components as dmc
    except ImportError as error:
        raise RuntimeError("configure_dmc requires dash-mantine-components>=2.6.0") from error

    pre_render_color_scheme = getattr(dmc, "pre_render_color_scheme", None)
    if pre_render_color_scheme is None:
        raise RuntimeError("configure_dmc requires dash-mantine-components>=2.6.0")

    theme = dmc.DEFAULT_THEME
    changes.setdefault("background", theme["white"])
    changes.setdefault("dark_background", theme["colors"]["dark"][7])
    changes.setdefault("pending_selector", None)

    global _mantine_prerender_registered
    with _CONFIG_LOCK:
        if not _mantine_prerender_registered:
            pre_render_color_scheme()
            _mantine_prerender_registered = True

    return configure(**changes)


def configure_dac(**changes: Any) -> StartupLoadingConfig:
    """Configure startup colors for Dash Ant Design.

    Explicit keyword arguments override the integration defaults, including
    ``background`` and ``dark_background`` when the application's Ant Design
    theme customizes its light or dark background token.
    """

    changes.setdefault("background", _ANTD_LIGHT_BACKGROUND)
    changes.setdefault("dark_background", _ANTD_DARK_BACKGROUND)
    return configure(**changes)


def configure_fac(**changes: Any) -> StartupLoadingConfig:
    """Configure startup colors for feffery-antd-components.

    Explicit keyword arguments override the integration defaults, including
    ``background`` and ``dark_background`` when the application's
    ``AntdConfigProvider`` customizes its light or dark theme tokens.
    """

    changes.setdefault("background", _ANTD_LIGHT_BACKGROUND)
    changes.setdefault("dark_background", _ANTD_DARK_BACKGROUND)
    return configure(**changes)


def get_config() -> StartupLoadingConfig:
    """Return the active immutable configuration."""

    with _CONFIG_LOCK:
        return _config


def reset_config() -> StartupLoadingConfig:
    """Restore the default configuration, primarily for tests."""

    global _config
    with _CONFIG_LOCK:
        _config = _DEFAULT_CONFIG
        return _config


def _client_config(config: StartupLoadingConfig) -> dict[str, Any]:
    values = asdict(config)
    return {
        "rootSelector": values["root_selector"],
        "requiredSelectors": list(values["required_selectors"]),
        "pendingSelector": values["pending_selector"],
        "timeoutMs": values["timeout_ms"],
        "minimumDisplayMs": values["minimum_display_ms"],
        "fadeDurationMs": values["fade_duration_ms"],
    }


def _theme_config(config: StartupLoadingConfig) -> dict[str, Any]:
    return {
        "themeMode": config.theme_mode,
        "dashThemeComponentId": config.dash_theme_component_id,
    }


def _overlay_html(config: StartupLoadingConfig) -> str:
    client_config = escape(
        json.dumps(_client_config(config), ensure_ascii=False, separators=(",", ":")),
        quote=True,
    )
    overlay_id = escape(config.overlay_id, quote=True)
    aria_label = escape(config.aria_label, quote=True)
    classes = ["dash-loading"]
    if config.hide_default_loading:
        classes.append("dash-loading--hide-default")
    class_name = " ".join(classes)
    styles = {
        "--dash-loading-background": config.background,
        "--dash-loading-dark-background": config.dark_background,
        "--dash-loading-color": config.color,
        "--dash-loading-dark-color": config.dark_color,
        "--dash-loading-size": f"{config.spinner_size_px}px",
        "--dash-loading-stroke": f"{config.spinner_stroke_px}px",
        "--dash-loading-fade-duration": f"{config.fade_duration_ms}ms",
        "--dash-loading-z-index": str(config.z_index),
    }
    style = escape(";".join(f"{name}:{value}" for name, value in styles.items()), quote=True)
    loader = config.custom_loader_html
    if loader is None:
        loader = '<span class="dash-loading__spinner" aria-hidden="true"></span>'

    return (
        f'<div id="{overlay_id}" class="{class_name}" {_OVERLAY_MARKER} '
        f'data-config="{client_config}" role="status" aria-live="polite" '
        f'aria-label="{aria_label}" aria-busy="true" style="{style}">'
        f'<div class="dash-loading__content">{loader}</div>'
        "</div>"
    )


@lru_cache(maxsize=2)
def _resource_text(name: str) -> str:
    return files("dash_startup_loading_plugin").joinpath("resources", name).read_text(encoding="utf-8").strip()


def _inline_head_resources(app_index: str, config: StartupLoadingConfig) -> str:
    theme_config = json.dumps(_theme_config(config), ensure_ascii=False, separators=(",", ":"))
    resources = (
        '<style data-dash-loading-resource="style">'
        f"{_resource_text('loading.css')}"
        "</style>"
        '<script data-dash-loading-resource="theme">'
        f"window.__dashLoadingThemeConfig={theme_config};"
        f"{_resource_text('theme.js')}"
        "</script>"
    )
    head_end = _HEAD_END_PATTERN.search(app_index)
    if head_end is not None:
        return app_index[: head_end.start()] + resources + app_index[head_end.start() :]
    return resources + app_index


def _inject_overlay(app_index: str) -> str:
    config = get_config()
    if not config.enabled or _OVERLAY_MARKER in app_index:
        return app_index

    body_match = _BODY_PATTERN.search(app_index)
    if body_match is None:
        return app_index
    app_index = _inline_head_resources(app_index, config)
    body_match = _BODY_PATTERN.search(app_index)
    assert body_match is not None
    position = body_match.end()
    script = f'<script data-dash-loading-resource="script">{_resource_text("loading.js")}</script>'
    return app_index[:position] + _overlay_html(config) + script + app_index[position:]


@hooks.index(priority=100)
def inject_startup_loading(app_index: str) -> str:
    """Inject the pre-React overlay into the final HTML document."""

    return _inject_overlay(app_index)


def _configure_installed_integrations() -> StartupLoadingConfig:
    """Apply defaults for supported component libraries already installed."""

    if find_spec("dash_antd_components") is not None:
        return configure_dac()
    return get_config()


_configure_installed_integrations()
