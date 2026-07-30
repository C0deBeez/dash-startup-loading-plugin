from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_readmes_use_current_selector_and_installation_examples():
    english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    for readme in (english, chinese):
        assert "#header" in readme
        assert "#sidebar-menu" in readme
        assert "pending_selector" in readme
        assert "pip install dash-ant-design" in readme
        assert "pip install feffery-antd-components" in readme
        assert "usage-header" not in readme
        assert "usage-sidebar-menu" not in readme
        assert "dash-ant-design  # Python 3.10+" not in readme
        assert "feffery-antd-components>=0.4.0" not in readme


def test_readmes_link_to_each_other():
    english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert "[简体中文](README.zh-CN.md)" in english
    assert "[English](README.md)" in chinese


def test_packaged_chinese_readme_matches_project_readme():
    project_readme = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    packaged_readme = (
        PROJECT_ROOT
        / "src"
        / "dash_startup_loading_plugin"
        / "README.zh-CN.md"
    ).read_text(encoding="utf-8")

    assert packaged_readme == project_readme
