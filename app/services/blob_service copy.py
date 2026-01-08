from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from app.config import (
    AZURE_STORAGE_ACCOUNT_NAME,
    AZURE_STORAGE_ACCOUNT_KEY,
    AZURE_STORAGE_CONTAINER_NAME,
    AZURE_STORAGE_PROCESSED_CONTAINER_NAME
)

CONTAINER_NAME = "documents"

def get_blob_service_client():
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={AZURE_STORAGE_ACCOUNT_NAME};AccountKey={AZURE_STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    return BlobServiceClient.from_connection_string(connection_string)

def save_processed_json(file_name: str, json_data: str):
    """
    전처리된 JSON 문자열을 processed 컨테이너(kkuldanji-mvp-processed)에 저장합니다.
    """
    try:
        # JSON 문자열을 bytes로 변환
        data_bytes = json_data.encode('utf-8')
        return upload_to_blob(file_name, data_bytes, container_name=AZURE_STORAGE_PROCESSED_CONTAINER_NAME)
    except Exception as e:
        print(f"[Error] Failed to save processed JSON: {e}")
        raise e
    
def upload_to_blob(file_name: str, file_data: bytes) -> str:
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    
    # 컨테이너 없으면 생성
    try:
        container_client.create_container()
    except: 
        pass
    
    blob_client = container_client.get_blob_client(file_name)
    blob_client.upload_blob(file_data, overwrite=True)
    
    # SAS 토큰 생성 (1시간 유효)
    sas_token = generate_blob_sas(
        account_name=AZURE_STORAGE_ACCOUNT_NAME,
        container_name=CONTAINER_NAME,
        blob_name=file_name,
        account_key=AZURE_STORAGE_ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    
    # SAS 토큰이 포함된 URL 반환
    blob_url_with_sas = f"{blob_client.url}?{sas_token}"
    return blob_url_with_sas