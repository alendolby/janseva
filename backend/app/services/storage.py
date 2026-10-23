from pathlib import Path
from uuid import uuid4
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException
from app.core.config import settings
import boto3

MIMES={"JPEG":("image/jpeg",".jpg"),"PNG":("image/png",".png")}
def validate(data,filename):
    if not data or len(data)>settings().max_upload_bytes: raise HTTPException(413,"File is empty or exceeds 10 MB")
    suffix=Path(filename or "").suffix.lower()
    if data.startswith(b"%PDF-"):
        mime,ext="application/pdf",".pdf"
        if b"%%EOF" not in data[-2048:] or any(x in data for x in [b"/JavaScript",b"/JS",b"/Launch",b"/EmbeddedFile"]):
            raise HTTPException(422,"PDF is invalid or contains active content")
    else:
        try:
            with Image.open(BytesIO(data)) as im:
                if im.width*im.height>25_000_000: raise HTTPException(422,"Image resolution is too large")
                mime,ext=MIMES[im.format];im.verify()
            # Re-encode to remove metadata and trailing polyglot content.
            with Image.open(BytesIO(data)) as im:
                out=BytesIO();im.convert("RGB").save(out,format="JPEG" if ext==".jpg" else "PNG");data=out.getvalue()
        except (UnidentifiedImageError,KeyError,OSError,Image.DecompressionBombError):
            raise HTTPException(422,"Only valid JPG, PNG and passive PDF evidence is accepted")
    if suffix not in ({".jpg",".jpeg"} if ext==".jpg" else {ext}):
        raise HTTPException(422,"File extension does not match content")
    return data,mime,ext

def client():
    c=settings();return boto3.client("s3",endpoint_url=c.storage_endpoint,
        aws_access_key_id=c.storage_access_key,aws_secret_access_key=c.storage_secret_key)
def store(data,ext):
    c=settings();key=uuid4().hex+ext
    if c.storage_mode=="s3":client().put_object(Bucket=c.storage_bucket,Key=key,Body=data)
    else:
        path=Path(c.upload_dir);path.mkdir(parents=True,exist_ok=True);(path/key).write_bytes(data)
    return key

def fetch(key):
    if settings().storage_mode=="s3":return client().get_object(Bucket=settings().storage_bucket,Key=key)["Body"].read()
    return (Path(settings().upload_dir)/key).read_bytes()
