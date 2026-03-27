import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

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
    # Khắc phục triệt để lỗi xung đột biến môi trường trên Đám mây
    if not os.getenv("RENDER"):
        load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key == "nhap-claude-api-key":
        return {
            "status": "error",
            "message": "Chưa có API Key Claude. Hãy lấy Key từ console.anthropic.com và điền vào."
        }

    client = AsyncAnthropic(api_key=api_key)

    system_prompt = """
    Bạn là IQI_RealEstateAI, một hệ thống chuyên gia đầu tư phân tích thông minh dựa trên quy trình M1 đến M7.
    Dữ liệu cần xuất ra là dạng JSON với cấu trúc bắt buộc sau đây (không phân tích dài dòng, gửi đúng cấu trúc JSON thô):
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
        response = await client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=1000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        result_content = response.content[0].text
        return json.loads(result_content)

    except Exception as e:
        return {
            "status": "error",
            "message": "Lỗi kết nối Claude API: " + str(e)
        }
