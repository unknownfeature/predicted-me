import boto3

from e2e.common import base_url, get_headers
import requests
presign_path = base_url + '/presign'

s3_client = boto3.client('s3')

def stream_s3_to_presigned_url(
        source_bucket: str,
        source_key: str,
        jwt: str) -> str:

     presigned_url_response = requests.get(presign_path + f'?extension={source_key[source_key.rindex('.'):]}&method=put' , get_headers(jwt))
     if not presigned_url_response.ok:
         raise Exception('Presigned URL failed ' + presigned_url_response.text)
     presigned_url = presigned_url_response.json()['url']
     key = presigned_url_response.json()['key']

     assert key is not None
     content_type = presigned_url_response.json()['content_type']

     s3_object = s3_client.get_object(Bucket=source_bucket, Key=source_key)

     data_stream = s3_object['Body']


     http_response = requests.put(
         presigned_url,
         data=data_stream,
         headers={'Content-Type': content_type}
     )

     if http_response.status_code == 200:
         return key
     else:
         raise Exception('Presigned URL failed ' + presigned_url_response.text)

def delete_from_bucket(key: str, jwt: str):
    presigned_url_response = requests.get(presign_path +  f'?key={key}&method=delete',  get_headers(jwt))
    if not presigned_url_response.ok:
        raise Exception('Presigned URL failed ' + presigned_url_response.text)
    response = requests.delete(presigned_url_response.json()['url'])
    if not response.ok:
        raise Exception('Presigned URL deletion failed ' + presigned_url_response.text)

