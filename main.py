import os
import json
import re
import datetime
from fastapi import FastAPI, Response, Request
from weasyprint import HTML

app = FastAPI()

def clean_text(text):
    """Xóa các trích dẫn dạng [1], [2] và ký tự markdown dư thừa"""
    if not isinstance(text, str): 
        return str(text) if text else ""
    # Xóa [1], [2], [1, 2]
    text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
    # Xóa dấu sao và gạch dưới của Markdown
    return text.replace("**", "").replace("_", "").strip()

def extract_json_safe(raw_str):
    """Tìm khối { ... } bên trong văn bản thô"""
    try:
        match = re.search(r'(\{.*\})', raw_str, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(raw_str)
    except Exception:
        return None

@app.post("/generate-pdf")
async def generate_pdf(request: Request):
    # Nhận dữ liệu thô từ Make.com để tránh lỗi 422
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    
    data = extract_json_safe(body_str)
    if not data:
        return Response(content="Lỗi: Không tìm thấy dữ liệu JSON hợp lệ", status_code=400)

    today = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Chuẩn bị HTML nội dung
    world_list = "".join([f"<li>{clean_text(x)}</li>" for x in data.get('world_summary', [])])
    vn_list = "".join([f"<li>{clean_text(x)}</li>" for x in data.get('vn_summary', [])])
    biz_list = "".join([f"<li>{clean_text(x)}</li>" for x in data.get('biz_recommendations', [])])
    
    regions_html = "".join([
        f"<div style='margin-bottom:10px;'><b>{r.get('name')}:</b> {clean_text(r.get('data'))}<br>"
        f"<i style='color:#555;'>{clean_text(r.get('analysis'))}</i></div>" 
        for r in data.get('world_regions', [])
    ])

    html_template = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 20mm 15mm; @bottom-right {{ content: "Trang " counter(page); font-size: 9pt; }} }}
            body {{ font-family: 'Helvetica', sans-serif; font-size: 10.5pt; line-height: 1.6; color: #333; }}
            .logo {{ font-weight: bold; font-size: 16pt; color: #C00000; border: 2px solid #C00000; padding: 5px 10px; display: inline-block; }}
            .banner {{ background-color: #C00000; color: white; padding: 20px; margin: 20px 0; border-radius: 4px; }}
            h2 {{ font-size: 14pt; color: #C00000; border-bottom: 2px solid #C00000; text-transform: uppercase; margin-top: 25px; }}
            .box {{ background: #f9f9f9; padding: 12px; border-left: 4px solid #C00000; margin: 10px 0; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="logo">CIBG MARKET ANALYSIS</div>
        <div class="banner">
            <h1 style="margin:0; font-size:18pt;">NHỊP ĐẬP THỊ TRƯỜNG: {data.get('week_number', 'HÀNG TUẦN')}</h1>
            <p style="margin:5px 0 0 0;">Thời gian: {data.get('date_range', today)} | Trạng thái: <b>{data.get('sentiment', 'N/A')}</b></p>
        </div>

        <section>
            <h2>A. KINH TẾ THẾ GIỚI</h2>
            <p><b>Tiêu điểm nóng:</b> {clean_text(data.get('world_hot_spot'))}</p>
            <ul>{world_list}</ul>
            <div class="box">{regions_html}</div>
        </section>

        <section>
            <h2>B. KINH TẾ VIỆT NAM</h2>
            <ul>{vn_list}</ul>
            <p><b>Vĩ mô (GDP/Lạm phát):</b> {clean_text(data.get('vn_growth_inflation'))}</p>
            <div class="box">
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
    
    pdf = HTML(string=html_template).write_pdf()
    return Response(content=pdf, media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
