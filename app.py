import os

import aws_cdk as cdk
import modules.vpc_stack as vpc
import modules.db_stack as db

from modules.constants import *
from dotenv import load_dotenv

load_dotenv()

app = cdk.App()
env = cdk.Environment(account=os.getenv(aws_account), region=os.getenv(aws_region))
vpc_stack = vpc.PmVpcStack(app,  env=env)
db_stack = db.PmDbStack(app,  vpc_stack, env=env)

bastion_stack = PmBastionStack(app, 'PmBastionStack', vpc_stack, env=env)
cognito_stack = PmCognitoStack(app, 'PmCognitoStack', env=env)
async_stack = PmAsyncStack(app, 'PmAsyncStack', env=env)
functions_stack = PmFunctionsStack(app, 'PmFuncStack', db_stack, cognito_stack, async_stack, vpc_stack=vpc_stack,
                                   env=env)
api_stack = PmApiStack(app, 'PmApiStack', cognito_stack, functions_stack, env=env)

app.synth()
