import os

import aws_cdk as cdk
from dotenv import load_dotenv

from modules.image_processing_stack import PmImageProcessingStack
from modules.api_stack import PmApiStack
from modules.async_stack import PmAsyncStack
from modules.bastion_stack import PmBastionStack
from modules.cognito_stack import PmCognitoStack
from modules.db_stack import PmDbStack
from modules.functions_stack import PmFunctionsStack
from modules.vpc_stack import PmVpcStack
from modules.constants import *

load_dotenv()

app = cdk.App()
env = cdk.Environment(account=os.getenv(aws_account), region=os.getenv(aws_region))
vpc_stack = PmVpcStack(app, env=env)
db_stack = PmDbStack(app, vpc_stack, env=env)
bastion_stack = PmBastionStack(app, vpc_stack, env=env)
cognito_stack = PmCognitoStack(app, env=env)
async_stack = PmAsyncStack(app, env=env)
functions_stack = PmFunctionsStack(app, env=env)
api_stack = PmApiStack(app, cognito_stack, env=env)
image_processing_stack = PmImageProcessingStack(app, vpc_stack, db_stack, env=env)

app.synth()
