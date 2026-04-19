from fastapi import FastAPI, Response, Request
from weasyprint import HTML
import re
import datetime
import json
import os

app = FastAPI()

def clean_text(text):
    """Lọc sạch các ký tự markdown và trích dẫn [1] từ Gemini"""
    if not isinstance(text, str): 
        return str(text) if text else ""
    # Xóa các tham chiếu dạng [1], [2], [1, 2]
    text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
    # Xóa markdown đậm/nghiêng
    text = text.replace("**", "").replace("_", "")
    return text.strip()

def extract_json_payload(raw_str):
    """Tìm và bóc tách khối JSON từ chuỗi văn bản bất kỳ"""
    try:
        # Tìm nội dung nằm giữa { và } đầu tiên/cuối cùng
        match = re.search(r'(\{.*\})', raw_str, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(raw_str)
    except Exception:
        return None

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    # Lấy dữ liệu thô để xử lý lỗi format từ Gemini
    raw_body = await request.body()
    decoded_body = raw_body.decode("utf-8")
    
    data = extract_json_payload(decoded_body)
    if not data:
        return Response(content="Lỗi: Dữ liệu gửi sang không phải JSON hợp lệ", status_code=400)

    today = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Chuẩn bị danh sách HTML
    world_list = "".join([f"<li>{clean_text(x)}</li>" for x in data.get('world_summary', [])])
    vn_list = "".join([f"<li>{clean_text(x)}</li>" for x in data.get('vn_summary', [])])
    biz_list = "".join([f"<li>{clean_text(x)}</li>" for x in data.get('biz_recommendations', [])])
    
    regions_html = "".join([
        f"<div style='margin-bottom:8px;'><b>{r.get('name')}:</b> {clean_text(r.get('data'))}<br>"
        f"<i style='color:#666;'>{clean_text(r.get('analysis'))}</i></div>" 
        for r in data.get('world_regions', [])
    ])

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 15mm; @bottom-right {{ content: "Trang " counter(page); font-size: 9pt; }} }}
            body {{ font-family: 'Helvetica', sans-serif; font-size: 10pt; line-height: 1.5; color: #333; }}
            .header-box {{ border-bottom: 3px solid #C00000; padding-bottom: 10px; margin-bottom: 20px; }}
            .logo {{ font-weight: bold; font-size: 18pt; color: #C00000; letter-spacing: 1px; }}
            .banner {{ background-color: #C00000; color: white; padding: 15px; margin: 15px 0; border-radius: 4px; }}
            h2 {{ font-size: 13pt; color: #C00000; border-left: 5px solid #C00000; padding-left: 10px; text-transform: uppercase; margin-top: 25px; }}
            .data-grid {{ background: #f4f4f4; padding: 12px; border-radius: 4px; margin: 10px 0; border: 1px solid #ddd; }}
            ul {{ padding-left: 18px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="header-box">
            <div class="logo">CIBG MARKET INTELLIGENCE</div>
        </div>
        
        <div class="banner">
            <h1 style="margin:0; font-size:16pt;">{data.get('week_number', 'BÁO CÁO VĨ MÔ')}</h1>
            <p style="margin:5px 0 0 0;">Thời gian: {data.get('date_range', today)} | Trạng thái: <b>{data.get('sentiment', 'N/A')}</b></p>
        </div>

        <section>
            <h2>A. KINH TẾ THẾ GIỚI</h2>
            <p><b>Tiêu điểm nóng:</b> {clean_text(data.get('world_hot_spot'))}</p>
            <ul>{world_list}</ul>
            <div class="data-grid">{regions_html}</div>
        </section>

        <section>
            <h2>B. KINH TẾ VIỆT NAM</h2>
            <ul>{vn_list}</ul>
            <p><b>Tăng trưởng & Lạm phát:</b> {clean_text(data.get('vn_growth_inflation'))}</p>
            <div class="data-grid">
                <b>Thị trường tài chính:</b><br>
                • Tỷ giá: {clean_text(data.get('vn_exchange_rate'))}<br>
                • Lãi suất: {clean_text(data.get('vn_interest_rate'))}<br>
                • Vàng SJC: {clean_text(data.get('vn_gold'))}
            </div>
            <p><b>Triển vọng:</b> {clean_text(data.get('vn_outlook'))}</p>
        </section>

        <section>
            <h2>C. CHIẾN LƯỢC DOANH NGHIỆP</h2>
            <p><b>Tác động:</b> {clean_text(data.get('biz_impact'))}</p>
            <ul>{biz_list}</ul>
        </section>
    </body>
    </html>
    """
    
    pdf = HTML(string=html_content).write_pdf()
    return Response(content=pdf, media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
