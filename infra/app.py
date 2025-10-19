import os

import aws_cdk as cdk

from infra.pm.recurrent_stack import PmRecurrentStack
from pm.audio_stack import PmAudioStack
from pm.tagging_stack import PmTaggingStack
from pm.text_stack import PmTextStack
from pm.image_stack import PmImageStack
from pm.api_stack import PmApiStack
from pm.bastion_stack import PmBastionStack
from pm.cognito_stack import PmCognitoStack
from pm.db_stack import PmDbStack
from pm.vpc_stack import PmVpcStack
from shared.variables import *

# export PYTHONPATH=$PYTHONPATH:./infra=/modules:./shared:./backend
#  cdk synth --app  "python infra/app.py"
#  cdk deploy --all  --app  "python infra/app.py"

app = cdk.App()
env = cdk.Environment(account=os.getenv(aws_account), region=os.getenv(aws_region))

vpc_stack = PmVpcStack(app, env=env)
db_stack = PmDbStack(app, vpc_stack, env=env)
bastion_stack = PmBastionStack(app, db_stack, vpc_stack, env=env)
cognito_stack = PmCognitoStack(app, env=env)
tagging_stack = PmTaggingStack(app, db_stack, vpc_stack, env=env)
text_processing_stack = PmTextStack(app, vpc_stack, db_stack, bastion_stack, env=env)
image_processing_stack = PmImageStack(app, vpc_stack, db_stack, text_processing_stack, env=env)
audio_stack = PmAudioStack(app, vpc_stack, db_stack, text_processing_stack, env=env)
recurrent_stack = PmRecurrentStack(app, db_stack, vpc_stack, env=env)
api_stack = PmApiStack(app, cognito_stack, image_processing_stack, audio_stack, text_processing_stack, db_stack, vpc_stack, env=env)

app.synth()

