from aws_cdk import (
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
    RemovalPolicy, Duration
)
from constructs import Construct
from modules.constants import *




# class FanoutConfig

class PmAsyncStack(Stack):

    def __init__(self, scope: Construct, **kwargs) -> None:
        super().__init__(scope, Async.stack_name, **kwargs)

        # todo finish this or maybe delete
        self.text_processing_queue = sqs.Queue(self, Async.text_processing_queue_name,
                                               visibility_timeout=Duration.minutes(5))
        self.text_processing_dead_letter_queue = sqs.DeadLetterQueue(max_receive_count=10,
                                                                     queue=self.text_processing_queue)



        self.nutrients_queue = sqs.Queue(self, Async.nutrients_extraction_queue_name,
                                         visibility_timeout=Duration.minutes(3))
        self.nutrients_dead_letter_queue = sqs.DeadLetterQueue(max_receive_count=10, queue=self.nutrients_queue)

        self.csv_processing_queue = sqs.Queue(self, Async.csv_processing_queue_name,
                                              visibility_timeout=Duration.minutes(15))
        self.csv_processing_dead_letter_queue = sqs.DeadLetterQueue(max_receive_count=10,
                                                                    queue=self.csv_processing_queue)

        self.csv_errors_queue = sqs.Queue(self, '%s' % Async.errors_handling_queue_name,
                                          visibility_timeout=Duration.minutes(5))
        self.csv_errors_dead_letter_queue = sqs.DeadLetterQueue(max_receive_count=10,
                                                                queue=self.csv_errors_queue)

        self.csv_bucket = s3.Bucket(self, Async.csv_bucket_name,
                                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                    enforce_ssl=True,
                                    encryption=s3.BucketEncryption.S3_MANAGED,
                                    versioned=True,
                                    removal_policy=RemovalPolicy.DESTROY
                                    )



