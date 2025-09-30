import os

from shared.variables import Common
from aws_cdk import aws_lambda


def docker_code_asset(build_args: dict[str, str]) -> aws_lambda.DockerImageCode:
    return aws_lambda.DockerImageCode.from_image_asset(
        directory=Common.docker_path,
        file=Common.docker_file,
        build_args={Common.lib_dir_arg: Common.lib_dir,
                    Common.backend_dir_arg: Common.backend_dir,
                    Common.shared_path_arg: Common.shared_path,
                    } | build_args
    )
