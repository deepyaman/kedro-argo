import textwrap

import pytest
from typer.testing import CliRunner

import kedro_argo.plugin
from kedro_argo.plugin import app

runner = CliRunner()


@pytest.fixture
def mock_project(monkeypatch):
    monkeypatch.setattr(kedro_argo.plugin, "PACKAGE_NAME", "test_package")
    monkeypatch.setattr(
        kedro_argo.plugin,
        "pipelines",
        {
            "__default__": None,
            "dp": None,
        },
    )


def test_convert_default_pipeline(mock_project):
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "generateName: test_package---default---" in result.stdout
    assert (
        textwrap.indent(
            textwrap.dedent(
                """
                - name: pipeline
                  value: __default__
                """
            ),
            "    ",
        )
        in result.stdout
    )


def test_convert_registered_pipeline(mock_project):
    result = runner.invoke(app, ["--pipeline", "dp"])
    assert result.exit_code == 0
    assert "generateName: test_package-dp-" in result.stdout
    assert (
        textwrap.indent(
            textwrap.dedent(
                """
                - name: pipeline
                  value: dp
                """
            ),
            "    ",
        )
        in result.stdout
    )


def test_convert_unregistered_pipeline(mock_project):
    with pytest.raises(ValueError, match="Failed to find the pipeline named 'ds'."):
        runner.invoke(app, ["--pipeline", "ds"], catch_exceptions=False)
