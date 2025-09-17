from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv("endpoint")
AZURE_KEY = os.getenv("key")

client = DocumentIntelligenceClient(endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY))

file_path = "S00014311-4500072887-EGHU3633197.pdf"

with open(file_path, "rb") as f:
    # Read the bytes
    file_bytes = f.read()

# Prepare the AnalyzeDocumentRequest using bytes source
req = AnalyzeDocumentRequest(bytes_source=file_bytes)

poller = client.begin_analyze_document(
    model_id="prebuilt-read", 
    analyze_request=req
)
result = poller.result()

print(result.content)
