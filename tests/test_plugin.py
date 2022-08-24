import textwrap

import anyconfig
import pytest
import yaml
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
            "ds": None,
        },
    )


def test_convert_default_pipeline(mock_project):
    result = runner.invoke(app, ["docker/whalesay:latest"])
    assert result.exit_code == 0
    assert "generateName: test-package---default---" in result.stdout
    assert "entrypoint: kedro-run" in result.stdout
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
    result = runner.invoke(app, ["docker/whalesay:latest", "--pipeline", "dp"])
    assert result.exit_code == 0
    assert "generateName: test-package-dp-" in result.stdout
    assert "entrypoint: kedro-run" in result.stdout
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
    with pytest.raises(ValueError, match="Failed to find the pipeline named 'de'."):
        runner.invoke(
            app, ["docker/whalesay:latest", "--pipeline", "de"], catch_exceptions=False
        )


def test_convert_dependencies(mock_project):
    result = runner.invoke(
        app, ["docker/whalesay:latest", "--dependencies", "dp:,ds:dp"]
    )
    assert result.exit_code == 0
    assert "entrypoint: dag" in result.stdout
    manifest = yaml.full_load(result.stdout)
    [dag] = (
        template["dag"]
        for template in manifest["spec"]["templates"]
        if template["name"] == "dag"
    )
    dependencies = {task["name"]: task.get("depends") for task in dag["tasks"]}
    assert dependencies == {"dp": None, "ds": "dp"}


@pytest.fixture(params=["config.yml", "config.json"])
def mock_config(request, tmp_path):
    config_path = str(tmp_path / request.param)
    anyconfig.dump(
        {
            "convert": {
                "image": "docker/whalesay:latest",
                "pipeline": "dp",
                "dependencies": "dp:,ds:dp",
            }
        },
        config_path,
    )
    return config_path


@pytest.mark.parametrize("config_flag", ["--config", "-c"])
def test_convert_with_config(
    mock_project,
    config_flag,
    mock_config,
):
    result = runner.invoke(app, [config_flag, mock_config])
    assert result.exit_code == 0
    assert "generateName: test-package-dp-" in result.stdout
    assert "entrypoint: dag" in result.stdout
    assert "image: docker/whalesay:latest" in result.stdout


@pytest.fixture
def mock_config_with_params(mock_config, request):
    config = anyconfig.load(mock_config)
    config["convert"].update(request.param)
    anyconfig.dump(config, mock_config)
    return mock_config


@pytest.mark.parametrize(
    "mock_config_with_params,expected",
    [
        ({}, {}),
        ({"params": {"foo": "baz"}}, {"foo": "baz"}),
        ({"params": "foo:baz"}, {"foo": "baz"}),
        (
            {"params": {"foo": "123.45", "baz": "678", "bar": 9}},
            {"foo": "123.45", "baz": "678", "bar": 9},
        ),
    ],
    indirect=["mock_config_with_params"],
)
def test_convert_with_params_in_config(
    mock_project,
    expected,
    mock_config_with_params,
    mocker,
):
    mock_update_nested_dict = mocker.patch.object(
        kedro_argo.plugin, "_update_nested_dict"
    )
    result = runner.invoke(
        app, ["docker/whalesay:latest", "-c", mock_config_with_params]
    )
    assert result.exit_code == 0, result.stdout
    mock_update_nested_dict.assert_called_once_with(mocker.ANY, expected)


@pytest.mark.parametrize(
    "cli_arg,expected_extra_params",
    [
        ("foo:bar", {"foo": "bar"}),
        (
            "foo:123.45, bar:1a,baz:678. ,qux:1e-2,quux:0,quuz:",
            {
                "foo": 123.45,
                "bar": "1a",
                "baz": 678,
                "qux": 0.01,
                "quux": 0,
                "quuz": "",
            },
        ),
        ("foo:bar,baz:fizz:buzz", {"foo": "bar", "baz": "fizz:buzz"}),
        (
            "foo:bar, baz: https://example.com",
            {"foo": "bar", "baz": "https://example.com"},
        ),
        ("foo:bar,baz:fizz buzz", {"foo": "bar", "baz": "fizz buzz"}),
        ("foo:bar, foo : fizz buzz  ", {"foo": "fizz buzz"}),
        ("foo.nested:bar", {"foo": {"nested": "bar"}}),
        ("foo.nested:123.45", {"foo": {"nested": 123.45}}),
        (
            "foo.nested_1.double_nest:123.45,foo.nested_2:1a",
            {"foo": {"nested_1": {"double_nest": 123.45}, "nested_2": "1a"}},
        ),
    ],
)
def test_convert_extra_params(
    mock_project,
    mocker,
    cli_arg,
    expected_extra_params,
):
    mock_update_nested_dict = mocker.patch.object(
        kedro_argo.plugin, "_update_nested_dict"
    )
    result = runner.invoke(app, ["docker/whalesay:latest", "--params", cli_arg])
    assert result.exit_code == 0
    mock_update_nested_dict.assert_called_once_with(mocker.ANY, expected_extra_params)


@pytest.mark.parametrize("bad_arg", ["bad", "foo:bar,bad"])
def test_convert_bad_extra_params(bad_arg):
    result = CliRunner().invoke(app, ["docker/whalesay:latest", "--params", bad_arg])
    assert result.exit_code
    assert "Item `bad` must contain a key and a value separated by `:`" in result.stdout


@pytest.mark.parametrize("bad_arg", [":", ":value", " :value"])
def test_convert_bad_params_key(bad_arg):
    result = CliRunner().invoke(app, ["docker/whalesay:latest", "--params", bad_arg])
    assert result.exit_code
    assert "Parameter key cannot be an empty string" in result.stdout
