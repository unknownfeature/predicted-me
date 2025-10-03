import os

import aws_cdk as cdk

from stacks.tagging_stack import PmTaggingStack
from stacks.text_stack import PmTextStack
from stacks.image_stack import PmImageStack
from stacks.api_stack import PmApiStack
from stacks.bastion_stack import PmBastionStack
from stacks.cognito_stack import PmCognitoStack
from stacks.db_stack import PmDbStack
from stacks.vpc_stack import PmVpcStack
from shared.variables import Env


# export PYTHONPATH=$PYTHONPATH:./infra=/modules:./shared:./backend
#  cdk synth --app  "python infra/app.py"

app = cdk.App()
env = cdk.Environment(account=os.getenv(Env.aws_account), region=os.getenv(Env.aws_region))

vpc_stack = PmVpcStack(app, env=env)
db_stack = PmDbStack(app, vpc_stack, env=env)
bastion_stack = PmBastionStack(app, vpc_stack, env=env)
cognito_stack = PmCognitoStack(app, env=env)
api_stack = PmApiStack(app, cognito_stack, env=env)
tagging_stack = PmTaggingStack(app, db_stack, vpc_stack, env=env)
text_processing_stack = PmTextStack(app, vpc_stack, db_stack, tagging_stack, env=env)
image_processing_stack = PmImageStack(app, vpc_stack, db_stack, text_processing_stack, env=env)

app.synth()

