# dash-startup-loading-plugin

[English](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.md) |
[简体中文](https://github.com/C0deBeez/dash-startup-loading-plugin/blob/master/README.zh-CN.md)

一个基于 [Dash Hooks 插件规范](https://dash.plotly.com/dash-plugins-using-hooks)
的可安装插件，用于将 Dash 初始加载提示替换为可配置的全屏 loading 遮罩。

插件会在 React 挂载前，将 CSS 和 JavaScript 注入 Dash 的标准 index
文档。应用无需复制 assets，也无需替换 `index_string`。Dash 自带的
`<div class="_dash-loading">` 节点仍会保留。

## 环境要求

- Python 3.9 或更高版本
- Dash 3.0.3 或更高版本

## 安装

```bash
pip install "dash-startup-loading-plugin>=1.0.1"
```

Dash 会通过 `dash_hooks` entry point 自动发现插件。安装后，默认 loading
效果会自动启用，无需在应用中显式导入。

如果环境中安装了 Dash Ant Design（`dash_antd_components`），插件会自动
识别并应用与其亮色、暗色主题匹配的 loading 背景。

## 快速开始

默认配置无需编写插件相关代码：

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

如需自定义行为，请在创建 `Dash` 实例前调用 `configure()`：

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

## 组件库集成

各组件库不是本插件的依赖。应用只需单独安装实际使用的组件库。

### Dash Ant Design

插件会自动识别 Dash Ant Design。只有需要覆盖默认配置时，才需要调用
`configure_dac()`：

```bash
pip install dash-ant-design
```

本插件不限制 Dash Ant Design 的版本。请安装与应用所用 Python 和 Dash
版本兼容的版本。

```python
from dash_startup_loading_plugin import configure_dac

configure_dac(
    background="#f5f5f5",
    dark_background="#202020",
)
```

### Dash Mantine Components

`configure_dmc()` 会读取 Mantine 的当前默认主题，并注册其预渲染配色
hook：

```bash
pip install dash-mantine-components
```

```python
from dash_startup_loading_plugin import configure_dmc

configure_dmc()
```

### feffery-antd-components

使用 `configure_fac()` 使 loading 遮罩与 `AntdConfigProvider` 匹配：

```bash
pip install feffery-antd-components
```

本插件不固定 feffery-antd-components 的版本，兼容性由已安装的组件库决定。

```python
from dash_startup_loading_plugin import configure_fac

configure_fac(required_selectors=["#fac-app-ready"])
```

## 内置示例

安装包中包含四个可直接运行的示例：

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

组件库需要单独安装。如果所选示例无法导入对应组件库，命令会显示导入失败的
模块和安装命令。

所有示例都支持服务器参数：

```bash
dash-startup-loading-plugin examples.dash \
    --host 127.0.0.1 --port 8050 --debug
```

## 就绪判断

满足以下条件后，遮罩会关闭：

1. `root_selector` 已存在，且内部不再包含 `._dash-loading`。
2. 根节点中已有实际渲染内容。
3. `required_selectors` 中的所有选择器都已匹配到节点。
4. 根节点中已不存在匹配 `pending_selector` 的节点。
5. 上述状态连续保持两个动画帧。

`timeout_ms` 是强制关闭的安全兜底。`minimum_display_ms` 适用于正常就绪和
手动关闭，但不会延迟 timeout。

`pending_selector` 用于在异步或懒加载占位节点仍存在时延迟关闭遮罩。它只会
在 `root_selector` 内查找匹配节点。可以设置为应用自己的 CSS 选择器；如果
不需要检查占位节点，请设置为 `None`：

```python
configure(pending_selector="[data-async-placeholder]")
configure(pending_selector=None)
```

## 配置项

`configure(**changes)` 会更新进程级、不可变的 `StartupLoadingConfig`。

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `enabled` | `True` | 是否启用 index 注入。 |
| `overlay_id` | `"dash-loading"` | 注入遮罩的 ID。 |
| `aria_label` | `"Loading"` | 无障碍状态标签。 |
| `root_selector` | `"#react-entry-point"` | 用于观察渲染内容的根节点。 |
| `required_selectors` | `("#react-entry-point",)` | 关闭遮罩前必须存在的节点选择器。 |
| `pending_selector` | `"[data-dac-async-placeholder]"` | 在 `root_selector` 内检查；所有匹配节点消失后才允许关闭。设置为 `None` 可禁用。 |
| `timeout_ms` | `6000` | 强制关闭超时；设置为 `None` 可禁用。 |
| `minimum_display_ms` | `0` | 最短显示时间。 |
| `fade_duration_ms` | `160` | 淡出时长。 |
| `z_index` | `9999` | 遮罩层级。 |
| `background` | `"#ffffff"` | 亮色背景。 |
| `dark_background` | `"#0f0f0f"` | 暗色背景。 |
| `color` | `"#1677ff"` | 亮色 spinner 颜色。 |
| `dark_color` | `"#4096ff"` | 暗色 spinner 颜色。 |
| `theme_mode` | `"auto"` | 可选 `"auto"`、`"light"` 或 `"dark"`。 |
| `dash_theme_component_id` | `None` | 优先读取主题状态的 Dash 持久化组件 ID。 |
| `spinner_size_px` | `28` | Spinner 宽度和高度。 |
| `spinner_stroke_px` | `3` | Spinner 描边宽度。 |
| `hide_default_loading` | `True` | 遮罩存在时隐藏 `._dash-loading` 的视觉效果。 |
| `custom_loader_html` | `None` | 替换默认 spinner 的可信 HTML。 |

`custom_loader_html` 会原样插入页面，禁止传入任何不可信的用户输入。

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

## 浏览器 API

```javascript
// 重新检查就绪条件。
window.dashLoading.check();

// 关闭默认或指定遮罩。
window.dashLoading.finish();
window.dashLoading.finish("my-loading-overlay");
```

淡出前，遮罩会触发可冒泡的 `dash-loading:ready` 事件。
`event.detail.reason` 为 `"ready"`、`"timeout"` 或 `"manual"`。

```javascript
document.addEventListener("dash-loading:ready", function (event) {
    console.log(event.detail.reason);
});
```

## 注意事项

- Dash hooks 和插件配置是进程级的，同一进程应共用一套配置。
- 资源以内联方式注入；严格 CSP 部署需要允许相应的 style 和 script。
- 本插件只处理应用初始启动。后续 callback loading 请使用 `dcc.Loading`
  或其他针对 callback 的方案。

## License

MIT
