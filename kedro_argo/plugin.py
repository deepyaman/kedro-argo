import click
import typer
import typer.core
import yaml
from argo_workflows.model.container import Container
from argo_workflows.model.io_argoproj_workflow_v1alpha1_arguments import (
    IoArgoprojWorkflowV1alpha1Arguments,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_inputs import (
    IoArgoprojWorkflowV1alpha1Inputs,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_parameter import (
    IoArgoprojWorkflowV1alpha1Parameter,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_template import (
    IoArgoprojWorkflowV1alpha1Template,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow import (
    IoArgoprojWorkflowV1alpha1Workflow,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_spec import (
    IoArgoprojWorkflowV1alpha1WorkflowSpec,
)
from argo_workflows.model.object_meta import ObjectMeta
from kedro.framework.project import PACKAGE_NAME, pipelines

typer.core.rich = None  # https://github.com/kedro-org/kedro/issues/1752

_DEFAULT_BASE_IMAGE = "docker/whalesay:latest"


@click.group(name="Kedro-Argo")
def commands():
    pass  # pragma: no cover


@commands.group()
def argo():
    """Convert and run a pipeline on Kubernetes using Argo Workflows."""


app = typer.Typer()


@app.command()
def convert(
    name: str = typer.Option("__default__", "--pipeline", "-p"),
    package_path: typer.FileTextWrite = typer.Option("-", "--output", "-o"),
):
    """Convert a pipeline to an Argo Workflow, and save the manifest."""
    try:
        pipeline = pipelines[name]
    except KeyError as exc:
        raise ValueError(
            f"Failed to find the pipeline named '{name}'. "
            f"It needs to be generated and returned "
            f"by the 'register_pipelines' function."
        ) from exc

    manifest = IoArgoprojWorkflowV1alpha1Workflow(
        apiVersion="argoproj.io/v1alpha1",
        kind="Workflow",
        metadata=ObjectMeta(generateName=f"{PACKAGE_NAME}-{name.replace('_', '-')}-"),
        spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
            entrypoint="whalesay",
            arguments=IoArgoprojWorkflowV1alpha1Arguments(
                parameters=[
                    IoArgoprojWorkflowV1alpha1Parameter(
                        name="pipeline",
                        value=name,
                    )
                ]
            ),
            templates=[
                IoArgoprojWorkflowV1alpha1Template(
                    name="whalesay",
                    inputs=IoArgoprojWorkflowV1alpha1Inputs(
                        parameters=[
                            IoArgoprojWorkflowV1alpha1Parameter(name="pipeline")
                        ]
                    ),
                    container=Container(
                        image=_DEFAULT_BASE_IMAGE,
                        command=["cowsay"],
                        args=["kedro run --pipeline {{inputs.parameters.pipeline}}"],
                    ),
                )
            ],
        ),
    )

    package_path.write(yaml.dump(manifest.to_dict()))


typer_click_object = typer.main.get_command(app)

argo.add_command(typer_click_object, "convert")
