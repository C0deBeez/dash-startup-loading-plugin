"""Dash Mantine Components theme demonstration."""

from dash import Dash

from ..plugin import configure_dmc
from .cli import DemoDependencyError
from .shared import (
    DEMO_ACTION_TEXT,
    DEMO_DESCRIPTION,
    DEMO_READY_TEXT,
    DEMO_READY_TITLE,
    DEMO_TITLE,
)


def create_app() -> Dash:
    """Create the Dash Mantine Components example application."""

    try:
        import dash_mantine_components as dmc
    except ModuleNotFoundError as error:
        if error.name != "dash_mantine_components":
            raise
        raise DemoDependencyError(
            "Failed to import dash_mantine_components. "
            "Install it with: pip install dash-mantine-components"
        ) from error

    configure_dmc(
        required_selectors=["#mantine-app-ready"],
        minimum_display_ms=250,
        fade_duration_ms=180,
        color="#15aabf",
        dark_color="#66d9e8",
    )

    app = Dash(__name__)
    app.layout = dmc.MantineProvider(
        dmc.Container(
            dmc.Stack(
                [
                    dmc.Group(
                        [
                            dmc.Title(DEMO_TITLE, order=1),
                            dmc.ColorSchemeToggle(
                                id="color-scheme-toggle",
                                lightIcon=dmc.Text("☀", fz=18),
                                darkIcon=dmc.Text("☾", fz=18),
                                size="lg",
                                radius="xl",
                                color="cyan",
                            ),
                        ],
                        justify="space-between",
                        align="center",
                    ),
                    dmc.Text(DEMO_DESCRIPTION),
                    dmc.Paper(
                        dmc.Stack(
                            [
                                dmc.Title(DEMO_READY_TITLE, order=3),
                                dmc.Text(DEMO_READY_TEXT),
                                dmc.Button(DEMO_ACTION_TEXT, color="cyan"),
                            ]
                        ),
                        withBorder=True,
                        radius="md",
                        p="xl",
                    ),
                ],
                gap="xl",
            ),
            id="mantine-app-ready",
            size="md",
            py=64,
        ),
        defaultColorScheme="auto",
    )
    return app
