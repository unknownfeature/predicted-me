import os

import aws_cdk as cdk


from modules.tagging_stack import PmTaggingStack
from modules.text_processing_stack import PmTextStack
from modules.image_processing_stack import PmImageProcessingStack
from modules.api_stack import PmApiStack
from modules.bastion_stack import PmBastionStack
from modules.cognito_stack import PmCognitoStack
from modules.db_stack import PmDbStack
from modules.vpc_stack import PmVpcStack
from shared.variables import Env



app = cdk.App()
env = cdk.Environment(account=os.getenv(Env.aws_account), region=os.getenv(Env.aws_region))

vpc_stack = PmVpcStack(app, env=env)
db_stack = PmDbStack(app, vpc_stack, env=env)
bastion_stack = PmBastionStack(app, vpc_stack, env=env)
cognito_stack = PmCognitoStack(app, env=env)
api_stack = PmApiStack(app, cognito_stack, env=env)
tagging_stack = PmTaggingStack(app, db_stack, vpc_stack, env=env)
text_processing_stack = PmTextStack(app, vpc_stack, db_stack, tagging_stack, env=env)
image_processing_stack = PmImageProcessingStack(app, vpc_stack, db_stack, text_processing_stack, env=env)

app.synth()
