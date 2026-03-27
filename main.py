import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import google.generativeai as genai

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

class GenerateRequest(BaseModel):
    projectName: str
    locationName: str
    propertyType: str
    objective: str = ""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/style.css")
async def read_css():
    return FileResponse("style.css")

@app.get("/script.js")
async def read_js():
    return FileResponse("script.js")

@app.post("/api/generate")
async def generate_report(req: GenerateRequest):
    load_dotenv(override=True)
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "nhap-gemini-api-key-cua-ban":
        return {
            "status": "error",
            "message": "Chưa có API Key Google Gemini. Hãy lấy Key từ Google AI Studio và điền vào file .env"
        }

    # Cấu hình API key cho mỗi request
    genai.configure(api_key=api_key)

    system_prompt = """
    Bạn là IQI_RealEstateAI, một hệ thống chuyên gia đầu tư phân tích thông minh dựa trên quy trình M1 đến M7.
    Dữ liệu cần xuất ra là dạng JSON với cấu trúc bắt buộc sau đây (không được thêm văn bản thừa hay code box markdown, chỉ xuất chuỗi JSON thô hợp lệ):
    {
      "status": "success",
      "project": "TÊN BĐS CHUẨN HOÁ",
      "financials": {
        "yield": "Lợi suất cho thuê (chỉ ghi số)",
        "irr": "Chỉ số IRR 5 năm (chỉ ghi số)",
        "price_per_m2": "Giá/m2 (chỉ ghi số)"
      },
      "persona": "Tên Chân dung khách mua cốt lõi (M4)",
      "persona_desc": "Mô tả ngắn gọn nhu cầu và nỗi đau của họ",
      "sale_script": "Kịch bản (M5) gọi điện chốt sale cực kỳ mạnh mẽ (khoảng 2 câu)",
      "score": "Điểm đầu tư chấm trên 10 (Ví dụ: 8.5)"
    }
    
    Hãy dùng trình độ suy luận logic thời gian thực vào tháng 3/2026, để xuất ra JSON sao cho chính xác nhất với thông tin được khách yêu cầu. Hãy ước tính nếu bạn không có dữ liệu thực tế tuyệt đối, nhưng phải cực kỳ logic thị trường.
    """

    user_prompt = f"""
    Dự án / Tài sản: {req.projectName}
    Khu vực: {req.locationName}
    Loại hình: {req.propertyType}
    Mục tiêu thêm: {req.objective}
    """

    try:
        # Sử dụng model Gemini 2.5 Flash rất phù hợp cho response nhanh và chính xác
        # Ép model trả về JSON thông qua generation_config
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json", "temperature": 0.7}
        )
        
        # Merge prompt lại vì Gemini SDK thiết kế cho việc nối chuỗi dễ dàng ở mode sinh chuỗi
        full_prompt = system_prompt + "\n\n=== USER INPUT ===\n" + user_prompt
        
        response = model.generate_content(full_prompt)
        
        result_content = response.text
        return json.loads(result_content)

    except Exception as e:
        return {
            "status": "error",
            "message": "Lỗi kết nối Gemini API: " + str(e)
        }
