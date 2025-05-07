from aws_cdk import (
    Stack
)
from constants import *
from constructs import Construct


class PmFunctionsStack(Stack):


    def __init__(self, scope: Construct,
                 **kwargs) -> None:
        super().__init__(scope, Func.stack_name, **kwargs)
