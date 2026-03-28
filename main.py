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

@app.get("/api/debug-env")
async def debug_env():
    # An toàn: Trả về 5 ký tự đầu của API key để kiểm tra xem Render có thực sự đẩy Biến lên không.
    val = os.getenv("GEMINI_API_KEY", "TRONG_KHONG_CO_GI")
    masked = val[:5] + "..." if val != "TRONG_KHONG_CO_GI" else val
    return {
        "status": "debug",
        "has_render_var": "RENDER" in os.environ,
        "gemini_key_starts_with": masked,
        "all_keys": list(os.environ.keys())
    }

@app.post("/api/generate")
async def generate_report(req: GenerateRequest):
    # Dùng Google Gemini 1.5 Pro
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    if not api_key:
        return {
            "status": "error",
            "message": "Chưa có GEMINI_API_KEY trên hệ thống Render."
        }

    try:
        genai.configure(api_key=api_key)
        
        # Chọn gemini-pro (Bản gốc siêu ổn định, không bị lỗi 404 v1beta)
        model = genai.GenerativeModel('gemini-pro')
        
        system_prompt = f"""Bạn là một chuyên gia phân tích Bất động sản AI cấp cao tại nhóm IQI... (Đóng vai Giám đốc IQI).
        Hãy trả về kết quả định dạng JSON nghiêm ngặt theo đúng cấu trúc yêu cầu.
        Dữ liệu cần xuất ra là dạng JSON với cấu trúc bắt buộc sau đây (không phân tích dài dòng, gửi đúng cấu trúc JSON thô):
        {{
          "status": "success",
          "project": "TÊN BĐS CHUẨN HOÁ",
          "financials": {{
            "yield": "Lợi suất cho thuê (chỉ ghi số)",
            "irr": "Chỉ số IRR 5 năm (chỉ ghi số)",
            "price_per_m2": "Giá/m2 (chỉ ghi số)"
          }},
          "persona": "Tên Chân dung khách mua cốt lõi (M4)",
          "persona_desc": "Mô tả ngắn gọn nhu cầu và nỗi đau của họ",
          "sale_script": "Kịch bản (M5) gọi điện chốt sale cực kỳ mạnh mẽ (khoảng 2 câu)",
          "score": "Điểm đầu tư chấm trên 10 (Ví dụ: 8.5)"
        }}
        
        Hãy dùng trình độ suy luận logic thời gian thực vào tháng 3/2026, để xuất ra JSON sao cho chính xác nhất với thông tin được khách yêu cầu. Hãy ước tính nếu bạn không có dữ liệu thực tế tuyệt đối, nhưng phải cực kỳ logic thị trường.
        """
        
        user_prompt = f"""
        Phân tích dự án: {req.projectName}
        Khu vực: {req.locationName}
        Loại hình: {req.propertyType}
        Yêu cầu thêm: {req.objective}
        Trả về JSON. Mọi khóa phải giống hệt như yêu cầu, không thêm bớt markdown ```json.
        """
        
        response = model.generate_content(
            system_prompt + "\n\n" + user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
            )
        )
        
        # Parse JSON
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        return json.loads(result_text.strip())

    except Exception as e:
        return {
            "status": "error",
            "message": "Lỗi kết nối Gemini API: " + str(e)
        }
