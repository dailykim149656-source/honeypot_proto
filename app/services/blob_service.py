from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from app.config import AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY, ENVIRONMENT
from azure.identity import DefaultAzureCredential
import os

# ===== Blob 클라이언트 초기화 =====

_blob_client = None

def get_blob_client():
    """Blob Service Client (싱글톤)"""
    global _blob_client
    if _blob_client is None:
        if ENVIRONMENT == "development":
            # 로컬: 연결 문자열 사용
            connection_string = f"DefaultEndpointsProtocol=https;AccountName={AZURE_STORAGE_ACCOUNT_NAME};AccountKey={AZURE_STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
            _blob_client = BlobServiceClient.from_connection_string(connection_string)
        else:
            # 프로덕션: Managed Identity 사용
            credential = DefaultAzureCredential()
            _blob_client = BlobServiceClient(
                account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
                credential=credential
            )
    return _blob_client

# ===== 기존 함수들 (유지) =====

def upload_to_blob(file_name: str, file_data: bytes):
    """
    Blob Storage에 파일 업로드 (기존)
    SAS Token이 포함된 URL 반환
    """
    container_name = "kkuldanji-mvp-raw"  # 또는 config에서 가져오기
    
    try:
        client = get_blob_client()
        container_client = client.get_container_client(container_name)
        
        # 파일 업로드
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_data, overwrite=True)
        
        # SAS Token 생성 (1시간 유효)
        sas_token = generate_blob_sas(
            account_name=AZURE_STORAGE_ACCOUNT_NAME,
            container_name=container_name,
            blob_name=file_name,
            account_key=AZURE_STORAGE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        
        blob_url_with_sas = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{file_name}?{sas_token}"
        
        return blob_url_with_sas
    
    except Exception as e:
        print(f"❌ Blob upload failed: {e}")
        raise

def save_processed_json(file_name: str, json_str: str):
    """
    처리된 JSON을 Blob Storage에 저장
    """
    container_name = "kkuldanji-mvp-processed"
    
    try:
        client = get_blob_client()
        container_client = client.get_container_client(container_name)
        
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(json_str.encode('utf-8'), overwrite=True)
        
        print(f"✅ Processed JSON saved: {file_name}")
    
    except Exception as e:
        print(f"⚠️ Failed to save processed JSON: {e}")
        raise
