from aws_cdk import (
    Stack,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_notifications as s3n, RemovalPolicy, Duration
)
from constructs import Construct
from constants import *


class PmAsyncStack(Stack):

    def __init__(self, scope: Construct, **kwargs) -> None:
        super().__init__(scope, Async.stack_name, **kwargs)

        self.text_processing_queue = sqs.Queue(self, Async.text_processing_queue_name,
                                               visibility_timeout=Duration.minutes(5))
        self.text_processing_dead_letter_queue = sqs.DeadLetterQueue(max_receive_count=10,
                                                                     queue=self.text_processing_queue)

        self.image_processing_queue = sqs.Queue(self, Async.image_processing_queue_name,
                                                visibility_timeout=Duration.minutes(15))
        self.image_processing_dead_letter_queue = sqs.DeadLetterQueue(max_receive_count=10,
                                                                      queue=self.image_processing_queue)

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

        self.image_bucket = s3.Bucket(self, Async.media_bucket_name,
                                      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                      enforce_ssl=True,
                                      encryption=s3.BucketEncryption.S3_MANAGED,
                                      versioned=True,
                                      removal_policy=RemovalPolicy.DESTROY
                                      )
        self.image_bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                                 s3n.SqsDestination(self.image_processing_queue))
        self.csv_bucket = s3.Bucket(self, Async.csv_bucket_name,
                                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                    enforce_ssl=True,
                                    encryption=s3.BucketEncryption.S3_MANAGED,
                                    versioned=True,
                                    removal_policy=RemovalPolicy.DESTROY
                                    )
        self.csv_bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
                                               s3n.SqsDestination(self.csv_processing_queue),
                                               s3.NotificationKeyFilter(prefix=filter_media))
