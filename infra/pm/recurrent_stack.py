from aws_cdk import (
    Stack,
    aws_lambda as lmbd)
from constructs import Construct

from shared.variables import Env, Recurrent, Common, ScheduledFunction
from .constants import true
from .db_stack import PmDbStack
from .function_factories import FunctionFactoryParams, create_role_with_db_access_factory, schedule_cb_factory
from .util import create_function
from .vpc_stack import PmVpcStack


class PmRecurrentStack(Stack):

    def __init__(self, scope: Construct,  db_stack: PmDbStack, vpc_stack: PmVpcStack,
                 **kwargs) -> None:
        super().__init__(scope, Recurrent.stack_name, **kwargs)

        self.data_cleanup_lambda = self._create_scheduled_function_with_db(db_stack, vpc_stack, Recurrent.data_cleanup_function)

        self.occurrence_cleanup_lambda = self._create_scheduled_function_with_db(db_stack, vpc_stack,
                                                                                 Recurrent.occurrence_cleanup_function)

        self.data_generation_lambda = self._create_scheduled_function_with_db(db_stack, vpc_stack, Recurrent.data_generation_function)

        self.occurrence_generation_lambda = self._create_scheduled_function_with_db(db_stack, vpc_stack,
                                                                                    Recurrent.occurrence_generation_function)

    def _create_scheduled_function_with_db(self, db_stack: PmDbStack, vpc_stack: PmVpcStack,
                                           function_params: ScheduledFunction) -> lmbd.Function:
        return create_function(self, FunctionFactoryParams(
            function_params=function_params,
            build_args={
                Common.func_dir_arg: function_params.code_path,
                Common.install_mysql_arg: true,
            },
            environment={
                Env.db_secret_arn: db_stack.db_secret.secret_full_arn,
                Env.db_endpoint: db_stack.db_instance.db_instance_endpoint_address,
                Env.db_name: db_stack.db_instance.instance_identifier,
                Env.db_port: db_stack.db_instance.db_instance_endpoint_port,
            },
            role_supplier=create_role_with_db_access_factory(db_stack.db_proxy),
            and_then=schedule_cb_factory(self, function_params),
            vpc=vpc_stack.vpc,
        ))

