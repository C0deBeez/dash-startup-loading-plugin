"""Shared copy and theme controls for all bundled examples."""

DEMO_TITLE = "Dash startup loading plugin"
DEMO_DESCRIPTION = (
    "The startup loading overlay stays visible until the application layout "
    "is ready, then fades without replacing Dash's built-in loading node."
)
DEMO_READY_TITLE = "Application ready"
DEMO_READY_TEXT = (
    "Refresh this page to replay the startup loading effect. Theme-enabled "
    "examples also restore the selected color scheme before Dash mounts."
)
DEMO_ACTION_TEXT = "Example component"

THEME_OPTIONS = [
    {"label": "Follow system", "value": "system"},
    {"label": "Light", "value": "light"},
    {"label": "Dark", "value": "dark"},
]

MAIN_STYLE = {
    "boxSizing": "border-box",
    "minHeight": "100vh",
    "margin": 0,
    "padding": "64px max(24px, calc((100vw - 640px) / 2))",
}

PANEL_STYLE = {
    "marginTop": 24,
    "padding": 24,
    "border": "1px solid #d9d9d9",
    "borderRadius": 8,
}
