from __future__ import annotations

from scripts.coordination.control_plane.operator_console.console_ui import (
    render_console_html,
)


def test_ui_is_responsive_and_dependency_free() -> None:
    html = render_console_html()
    assert 'name="viewport"' in html
    assert "@media (max-width: 760px)" in html
    assert "https://" not in html
    assert "http://" not in html


def test_ui_exposes_required_mini6_sections() -> None:
    html = render_console_html()
    for heading in (
        "State snapshot",
        "Protected Terminal",
        "Assistant Dev Sandbox",
        "Checkpoint &amp; sealed result",
        "Promotion preview",
    ):
        assert heading in html


def test_ui_uses_existing_backend_action_names() -> None:
    html = render_console_html()
    for action in (
        "terminal_plan",
        "terminal_run",
        "sandbox_create",
        "sandbox_status",
        "checkpoint",
        "seal",
        "promotion_preview",
    ):
        assert action in html


def test_ui_does_not_expose_promotion_apply_or_git_release_controls() -> None:
    html = render_console_html()
    assert 'action("promotion_apply"' not in html
    assert 'action("commit"' not in html
    assert 'action("push"' not in html
    assert 'action("merge"' not in html
    assert 'action("release"' not in html
    assert "MINI-6 intentionally exposes no promotion-apply control" in html


def test_ui_discloses_non_authoritative_and_transport_boundary() -> None:
    html = render_console_html()
    assert "not</strong> execution/state authority" in html
    assert "no built-in authentication or TLS" in html
    assert "trusted tunnel or protected transport" in html
