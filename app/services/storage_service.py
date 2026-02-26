import boto3
import asyncio

from botocore.config import Config
from app.core.settings import settings 

s3_client = boto3.client(
    's3',
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY,
    aws_secret_access_key=settings.R2_SECRET_KEY,
    config=Config(signature_version='s3v4')
)

def _upload_to_r2(file_bytes: bytes, full_key: str, content_type: str) -> str:
    s3_client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=full_key,
        Body=file_bytes,
        ContentType=content_type
    )
    
    return f'{settings.R2_PUBLIC_URL}/{full_key}'

async def upload_file_to_r2(
    file_bytes: bytes, 
    folder: str, 
    file_name: str,
    content_type: str) -> str:
    
    full_key = f'{folder}/{file_name}'
    public_url = await asyncio.to_thread(_upload_to_r2, file_bytes, full_key, content_type)
    return public_url
