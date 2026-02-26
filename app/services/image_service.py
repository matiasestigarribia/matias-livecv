import os
import asyncio

from io import BytesIO
from PIL import Image

from fastapi import UploadFile

def _optimize_to_bytes(content: bytes, filename: str) -> tuple [bytes, str]:
    
    image = Image.open(BytesIO(content))
    
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA')
    
    image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
    
    base_name = os.path.splitext(filename)[0]
    safe_name = base_name.replace(' ', '_').lower()
    new_filename = f'{safe_name}.webp'
    
    output_buffer = BytesIO()
    image.save(output_buffer, format='WEBP', quality=80)
    webp_bytes = output_buffer.getvalue()
    
    return webp_bytes, new_filename

async def optimize_image_bytes(upload_file: UploadFile) -> tuple[bytes, str]:
    content = await upload_file.read()
    webp_bytes, new_filename = await asyncio.to_thread(_optimize_to_bytes, content, upload_file.filename)
    return webp_bytes, new_filename
