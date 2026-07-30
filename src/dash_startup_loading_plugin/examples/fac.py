"""feffery-antd-components theme persistence demonstration."""

from dash import Dash, Input, Output, clientside_callback, html

from ..plugin import configure_fac
from .cli import DemoDependencyError
from .shared import (
    DEMO_ACTION_TEXT,
    DEMO_DESCRIPTION,
    DEMO_READY_TEXT,
    DEMO_READY_TITLE,
    DEMO_TITLE,
    MAIN_STYLE,
    PANEL_STYLE,
    THEME_OPTIONS,
)


def create_app() -> Dash:
    """Create the feffery-antd-components example application."""

    try:
        import feffery_antd_components as fac
    except ModuleNotFoundError as error:
        if error.name != "feffery_antd_components":
            raise
        raise DemoDependencyError(
            "Failed to import feffery_antd_components. "
            "Install it with: pip install feffery-antd-components"
        ) from error

    configure_fac(
        required_selectors=["#fac-app-ready"],
        minimum_display_ms=250,
        fade_duration_ms=180,
    )

    app = Dash(__name__)
    app.layout = fac.AntdConfigProvider(
        html.Main(
            [
                html.H1(DEMO_TITLE),
                html.P(DEMO_DESCRIPTION),
                fac.AntdSegmented(
                    id="fac-theme-mode",
                    options=THEME_OPTIONS,
                    value="system",
                    block=True,
                    persistence=True,
                    persisted_props=["value"],
                    persistence_type="local",
                ),
                html.Section(
                    [
                        html.H2(DEMO_READY_TITLE),
                        html.P(DEMO_READY_TEXT),
                        fac.AntdButton(DEMO_ACTION_TEXT, type="primary"),
                    ],
                    style=PANEL_STYLE,
                ),
            ],
            id="fac-app-ready",
            style=MAIN_STYLE,
        ),
        id="fac-theme-provider",
        algorithm="default",
        locale="en-us",
    )

    clientside_callback(
        """function(mode) {
            const selected = mode || "system";
            const media = window.matchMedia("(prefers-color-scheme: dark)");

            try {
                localStorage.setItem("theme", JSON.stringify(selected));
            } catch (_) {}

            function applyDocumentScheme(dark) {
                document.documentElement.style.colorScheme = dark ? "dark" : "light";
            }

            const dark = selected === "dark"
                || (selected === "system" && media.matches);
            applyDocumentScheme(dark);

            if (!window.__dashLoadingFacThemeListener) {
                window.__dashLoadingFacThemeListener = function(event) {
                    let current = "system";
                    try {
                        current = JSON.parse(localStorage.getItem("theme")) || "system";
                    } catch (_) {}
                    if (current !== "system") return;
                    applyDocumentScheme(event.matches);
                    dash_clientside.set_props("fac-theme-provider", {
                        algorithm: event.matches ? "dark" : "default"
                    });
                };
                media.addEventListener(
                    "change",
                    window.__dashLoadingFacThemeListener
                );
            }

            return dark ? "dark" : "default";
        }""",
        Output("fac-theme-provider", "algorithm"),
        Input("fac-theme-mode", "value"),
    )
    return app
