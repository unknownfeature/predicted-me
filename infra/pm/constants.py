from aws_cdk import aws_iam as iam
true = 'True'
bedrock_invoke_policy_statement = iam.PolicyStatement(
                    actions=['bedrock:InvokeModel'],
                    resources=['*'],
                    effect=iam.Effect.ALLOW
                )