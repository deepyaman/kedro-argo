import click
import typer
import typer.core

from kedro.framework.project import pipelines

typer.core.rich = None  # https://github.com/kedro-org/kedro/issues/1752


@click.group(name="Kedro-Argo")
def commands():
    pass


@commands.group()
def argo():
    """Convert and run a pipeline on Kubernetes using Argo Workflows."""


app = typer.Typer()


@app.command()
def convert(name: str = typer.Option("__default__", "--pipeline", "-p")):
    """Convert a pipeline to an Argo Workflow, and save the manifest."""
    try:
        pipeline = pipelines[name]
    except KeyError as exc:
        raise ValueError(
            f"Failed to find the pipeline named '{name}'. "
            f"It needs to be generated and returned "
            f"by the 'register_pipelines' function."
        ) from exc

    print(pipeline)


typer_click_object = typer.main.get_command(app)

argo.add_command(typer_click_object, "convert")
