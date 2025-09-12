# from fastapi import APIRouter, UploadFile, File, HTTPException
# import os
# from app.services.process import process_file
# from app.core.config import UPLOAD_DIR
# from fastapi.responses import JSONResponse

# router = APIRouter()

# @router.post("/")
# async def upload_file(file: UploadFile = File(...), dataset_name: str = "test"):
#     upload_path = os.path.join(UPLOAD_DIR, dataset_name)
#     os.makedirs(upload_path, exist_ok=True)
#     file_path = os.path.join(upload_path, file.filename)

#     try:
#         with open(file_path, "wb") as f:
#             f.write(await file.read())
#         result = await process_file(file_path, dataset_name)
#         return JSONResponse(content={"message": f"File {file.filename} processed", "data": result})
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import json

from app.services.process import process_file
from app.core.config import UPLOAD_DIR
from app.core.db import get_db_connection

router = APIRouter()

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    model_prompt: str = Form("Extract all data."),
    example_schema: str = Form("{}")
):
    upload_path = os.path.join(UPLOAD_DIR, dataset_name)
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, file.filename)

    try:
        example_schema_dict = json.loads(example_schema)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in example_schema.")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT config_data FROM configurations WHERE id = %s", ('configuration',))
                result = cur.fetchone()
                config_data = result[0] if result else {"id": "configuration"}

                if dataset_name not in config_data:
                    config_data[dataset_name] = {
                        "model_prompt": model_prompt,
                        "example_schema": example_schema_dict
                    }

                    cur.execute(
                        "INSERT INTO configurations (id, config_data) VALUES (%s, %s) "
                        "ON CONFLICT (id) DO UPDATE SET config_data = EXCLUDED.config_data",
                        ('configuration', json.dumps(config_data))
                    )
                    conn.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
        result = await process_file(file_path, dataset_name)
        return JSONResponse(content={"message": f"File {file.filename} processed", "data": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


