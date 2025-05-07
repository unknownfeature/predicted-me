import os

import aws_cdk as cdk
import modules.vpc_stack as vpc
import modules.db_stack as db
import modules.bastion_stack as bastion
import modules.cognito_stack as cognito
import modules.async_stack as azync
import modules.functions_stack as func

from modules.constants import *
from dotenv import load_dotenv

load_dotenv()

app = cdk.App()
env = cdk.Environment(account=os.getenv(aws_account), region=os.getenv(aws_region))
vpc_stack = vpc.PmVpcStack(app,  env=env)
db_stack = db.PmDbStack(app,  vpc_stack, env=env)
bastion_stack = bastion.PmBastionStack(app,  vpc_stack, env=env)
cognito_stack = cognito.PmCognitoStack(app, env=env)
async_stack = azync.PmAsyncStack(app, env=env)
functions_stack = func.PmFunctionsStack(app, env=env)
api_stack = PmApiStack(app, 'PmApiStack', cognito_stack, functions_stack, env=env)

app.synth()
