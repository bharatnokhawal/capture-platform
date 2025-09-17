from app.core.db import get_db_connection
from app.services.ocr import extract_text
from app.services.ocr_llm import extract_text_llm
from app.services.azure_ocr import extract_text_azure
from app.services.gpt_extraction import extract_with_gemini
from psycopg2.extras import Json
from fastapi import HTTPException
from datetime import datetime
import json
import os
import re

def fetch_configuration():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT config_data FROM configurations WHERE id = %s", ('configuration',))
            result = cur.fetchone()
            return result[0] if result else {"id": "configuration"}

async def process_file(file_path, dataset_name):
    config = fetch_configuration()
    #prompt_template = config.get(dataset_name, {}).get("model_prompt", "Extract all data.")
    #example_schema = config.get(dataset_name, {}).get("example_schema", {})

    #ocr_output, num_pages = extract_text(file_path)
    ocr_output,num_pages = extract_text_azure(file_path)


    schema = """
{
  "DocumentDetails": {
    "DocumentType": "Invoice/Packing List",
    "DocumentNumber": "string",
    "DocumentDate": "YYYY-MM-DD",
    "ReferenceNumbers": {
      "OrderNumber": "string",
      "InvoiceNumber": "string",
      "PackingListNumber": "string",
      "CustomerReference": "string",
      "ExportDeclarationNumber": "string",
      "LetterOfCreditNumber": "string"
    },
    "Currency": "string",
    "Incoterms": {
      "Term": "string",
      "Place": "string",
      "Version": "Incoterms 2020"
    }
  },
  "Shipper": {
    "Name": "string",
    "Address": {
      "Street": "string",
      "City": "string",
      "PostalCode": "string",
      "Country": "string"
    },
    "Contact": {
      "Phone": "string",
      "Email": "string"
    },
    "TaxID": "string",
    "EORI": "string"
  },
  "Consignee": {
    "Name": "string",
    "Address": {
      "Street": "string",
      "City": "string",
      "PostalCode": "string",
      "Country": "string"
    },
    "Contact": {
      "Phone": "string",
      "Email": "string"
    },
    "TaxID": "string",
    "EORI": "string"
  },
  "Buyer": {
    "Name": "string",
    "Address": "string",
    "TaxID": "string"
  },
  "Receiver": {
    "Name": "string",
    "Address": {
      "Street": "string",
      "City": "string",
      "PostalCode": "string",
      "Country": "string"
    },
    "Email": "string",
    "POBox": "string",
    "District": "string"
  },
  "NotifyParty": {
    "Name": "string",
    "Address": "string",
    "Contact": "string"
  },
  "TransportDetails": {
    "ModeOfTransport": "Air/Ocean/Road/Rail",
    "CarrierName": "string",
    "VesselName": "string",
    "VoyageNumber": "string",
    "FlightNumber": "string",
    "PortOfLoading": "string",
    "PortOfDischarge": "string",
    "PlaceOfReceipt": "string",
    "PlaceOfDelivery": "string",
    "FinalDestination": "string",
    "LicensePlate": "string",
    "NationalityOfTransport": "string",
    "ContainerNumbers": ["string"],
    "SealNumbers": ["string"]
  },
  "GoodsDetails": [
    {
      "ProductNumber": "string",
      "Description": "string",
      "HSCode": "string",
      "OriginCountry": "string",
      "DestinationCountry": "string",
      "Quantity": "number",
      "Pieces": "number",
      "PackageType": "Carton/Box/Crate/Pallet",
      "MarksAndNumbers": "string",
      "NetWeight": "number",
      "GrossWeight": "number",
      "Volume": "number",
      "Dimensions": {
        "Length": "number",
        "Width": "number",
        "Height": "number"
      },
      "UnitPrice": "number",
      "TotalAmount": "number",
      "Currency": "string"
    }
  ],
  "Totals": {
    "TotalPackages": "number",
    "TotalPieces": "number",
    "TotalNetWeight": "number",
    "TotalGrossWeight": "number",
    "TotalVolume": "number",
    "TotalInvoiceValue": "number",
    "TotalCurrency": "string"
  },
  "PaymentDetails": {
    "PaymentTerms": "Prepaid/Collect",
    "PaymentMethod": "Bank Transfer / L/C / Credit",
    "BankDetails": {
      "BankName": "string",
      "AccountNumber": "string",
      "SWIFTCode": "string",
      "IBAN": "string"
    }
  },
  "Legal": {
    "Jurisdiction": "string",
    "LawApplicable": "string",
    "Clauses": [
      "string"
    ]
  },
  "Signatures": {
    "AuthorizedSignature": "string",
    "DateSigned": "YYYY-MM-DD",
    "PlaceSigned": "string"
  }
}
"""
    prompt = f"""

    first need to extract the text form this pdf and do this job
    

    You are an OCR document parser.

Extract all possible information from the provided document text (invoice/packing list).
Output the result as valid JSON strictly following the schema below. 

⚠️ Rules:
- Do not add, remove, or rename any keys.
- Preserve the same structure and field order.
- Replace "string"/"number" placeholders with extracted values.
- If a field is missing, write null.
- Always return valid JSON only.

    Schema:
    {schema} 

    OCR Output:
    {ocr_output}

    """

    gpt_output_raw = await extract_with_gemini(prompt,file_path=file_path)
    
    try:
        cleaned = gpt_output_raw.strip().strip("```json").strip("```")
        gpt_output = json.loads(cleaned)
    except Exception:
        gpt_output = {"raw": gpt_output_raw, "error": "Failed to parse JSON"}
    print(gpt_output)
    data = {
        'id': f"{dataset_name}/{os.path.basename(file_path)}",
        'properties': {
            'blob_name': f"{dataset_name}/{os.path.basename(file_path)}",
            'request_timestamp': datetime.utcnow().isoformat(),
            'blob_size': os.path.getsize(file_path),
            'num_pages': num_pages,
            'total_time_seconds': 0
        },
        'state': {
            'file_landed': True,
            'ocr_completed': bool(ocr_output),
            'gpt_extraction_completed': bool(gpt_output),
            'processing_completed': bool(ocr_output and gpt_output)
        },
        'extracted_data': {
            'ocr_output': ocr_output,
            'gpt_extraction_output': gpt_output
        }
    }

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (id, data) VALUES (%s, %s) "
                "ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data",
                (data['id'], Json(data))
            )
            conn.commit()

    return data
