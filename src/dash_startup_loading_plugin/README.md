# dash-startup-loading-plugin

[English](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.md) |
[简体中文](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.zh-CN.md)

An installable [Dash Hooks plugin](https://dash.plotly.com/dash-plugins-using-hooks)
that replaces Dash's initial loading presentation with a configurable
full-screen overlay.

The plugin injects its CSS and JavaScript into Dash's normal index document
before React mounts. Applications do not need to copy assets or replace
`index_string`, and Dash's built-in `<div class="_dash-loading">` remains in the
document.

## Requirements

- Python 3.9 or later
- Dash 3.0.3 or later

## Installation

```bash
pip install "dash-startup-loading-plugin>=1.0.1"
```

Dash discovers the plugin through its `dash_hooks` entry point. Installing the
package enables the default loading overlay without an explicit import.

When Dash Ant Design (`dash_antd_components`) is installed, the plugin detects
it automatically and applies matching light and dark loading backgrounds.

## Quick start

The default configuration requires no plugin-specific code:

```python
from dash import Dash, html

app = Dash(__name__)
app.layout = html.Main(
    [
        html.H1("My Dash app"),
        html.P("The overlay closes after this layout is ready."),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
```

Call `configure()` before creating `Dash` when custom behavior is needed:

```python
from dash import Dash, html
from dash_startup_loading_plugin import configure

configure(
    required_selectors=["#header", "#sidebar-menu"],
    pending_selector="[data-async-placeholder]",
    timeout_ms=6000,
    minimum_display_ms=250,
    fade_duration_ms=180,
)

app = Dash(__name__)
app.layout = html.Main(
    [
        html.Header("Header", id="header"),
        html.Nav("Sidebar", id="sidebar-menu"),
    ]
)
```

## Component-library integrations

Component libraries are not dependencies of this package. Install only the
libraries used by the application.

### Dash Ant Design

Dash Ant Design is detected automatically. `configure_dac()` is only required
to override its defaults:

```bash
pip install dash-ant-design
```

The plugin does not impose a Dash Ant Design version constraint. Use the
version compatible with the application's Python and Dash versions.

```python
from dash_startup_loading_plugin import configure_dac

configure_dac(
    background="#f5f5f5",
    dark_background="#202020",
)
```

### Dash Mantine Components

`configure_dmc()` uses Mantine's active default theme and registers its
pre-render color-scheme hook:

```bash
pip install dash-mantine-components
```

```python
from dash_startup_loading_plugin import configure_dmc

configure_dmc()
```

### feffery-antd-components

Use `configure_fac()` to match the loading overlay to
`AntdConfigProvider`:

```bash
pip install feffery-antd-components
```

The plugin does not pin a feffery-antd-components version. Compatibility is
determined by the installed component library.

```python
from dash_startup_loading_plugin import configure_fac

configure_fac(required_selectors=["#fac-app-ready"])
```

## Installed examples

The package includes four runnable examples:

```bash
# Dash
dash-startup-loading-plugin examples.dash

# Dash Mantine Components
dash-startup-loading-plugin examples.dash-mantine-components

# Dash Ant Design
dash-startup-loading-plugin examples.dash-ant-design

# feffery-antd-components
dash-startup-loading-plugin examples.feffery-antd-components
```

Install the selected example's component library separately. If it cannot be
imported, the command reports the failed module and the corresponding
installation command.

Server options are available on every example:

```bash
dash-startup-loading-plugin examples.dash \
    --host 127.0.0.1 --port 8050 --debug
```

## Readiness behavior

The overlay closes when:

1. `root_selector` exists and no longer contains `._dash-loading`.
2. The root contains rendered content.
3. Every `required_selectors` entry exists.
4. No `pending_selector` node remains under the root.
5. The conditions remain true for two animation frames.

`timeout_ms` is a forced-dismiss fallback. `minimum_display_ms` applies to
ready and manual dismissal, but does not delay a timeout.

`pending_selector` delays dismissal while any matching element remains inside
`root_selector`. It is useful for lazy or asynchronous placeholders that are
mounted before the real content. Set it to an application-specific CSS
selector, or use `None` when no pending-node check is needed:

```python
configure(pending_selector="[data-async-placeholder]")
configure(pending_selector=None)
```

## Configuration

`configure(**changes)` updates the process-wide immutable
`StartupLoadingConfig`.

| Option | Default | Description |
|---|---:|---|
| `enabled` | `True` | Enable index injection. |
| `overlay_id` | `"dash-loading"` | Injected overlay ID. |
| `aria_label` | `"Loading"` | Accessible status label. |
| `root_selector` | `"#react-entry-point"` | Root observed for rendered content. |
| `required_selectors` | `("#react-entry-point",)` | Selectors that must exist before dismissal. |
| `pending_selector` | `"[data-dac-async-placeholder]"` | Selector checked under `root_selector`; dismissal waits until all matches disappear. Use `None` to disable. |
| `timeout_ms` | `6000` | Forced-dismiss timeout; use `None` to disable. |
| `minimum_display_ms` | `0` | Minimum display time. |
| `fade_duration_ms` | `160` | Fade-out duration. |
| `z_index` | `9999` | Overlay stacking order. |
| `background` | `"#ffffff"` | Light background. |
| `dark_background` | `"#0f0f0f"` | Dark background. |
| `color` | `"#1677ff"` | Light spinner color. |
| `dark_color` | `"#4096ff"` | Dark spinner color. |
| `theme_mode` | `"auto"` | `"auto"`, `"light"`, or `"dark"`. |
| `dash_theme_component_id` | `None` | Preferred persisted Dash theme component. |
| `spinner_size_px` | `28` | Spinner width and height. |
| `spinner_stroke_px` | `3` | Spinner stroke width. |
| `hide_default_loading` | `True` | Hide the visual `._dash-loading` indicator while the overlay exists. |
| `custom_loader_html` | `None` | Trusted HTML replacing the default spinner. |

`custom_loader_html` is inserted verbatim and must never contain untrusted
user input.

## Python API

```python
from dash_startup_loading_plugin import (
    StartupLoadingConfig,
    configure,
    configure_dac,
    configure_fac,
    configure_dmc,
    get_config,
    reset_config,
)
```

## Browser API

```javascript
// Recheck readiness.
window.dashLoading.check();

// Dismiss the default or a custom overlay.
window.dashLoading.finish();
window.dashLoading.finish("my-loading-overlay");
```

Before fading out, the overlay emits a bubbling `dash-loading:ready` event.
`event.detail.reason` is `"ready"`, `"timeout"`, or `"manual"`.

```javascript
document.addEventListener("dash-loading:ready", function (event) {
    console.log(event.detail.reason);
});
```

## Notes

- Dash's hook and plugin configuration is process-wide. Use one configuration
  per process.
- Resources are inlined, so strict Content Security Policy deployments must
  allow the injected style and script.
- The overlay is only for initial application startup. Use `dcc.Loading` or
  another callback-specific pattern for later callback execution.

## License

MIT
