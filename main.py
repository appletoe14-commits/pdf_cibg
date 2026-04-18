from fastapi import FastAPI, Response, Body
from weasyprint import HTML
import re
import datetime

app = FastAPI()

def clean(text):
    if not isinstance(text, str): return str(text) if text else ""
    # Xóa cite và markdown
    text = re.sub(r"\]*\]", "", text)
    return text.replace("**", "").replace("_", "").strip()

@app.post("/generate-pdf")
async def generate_pdf(data: dict = Body(...)):
    today = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Logic bóc tách dữ liệu từ JSON của Gemini
    world_list = "".join([f"<li>{clean(x)}</li>" for x in data.get('world_summary', [])])
    regions_html = "".join([f"<p><b>{r.get('name')}:</b> {clean(r.get('data'))}<br><i>{clean(r.get('analysis'))}</i></p>" 
                            for r in data.get('world_regions', [])])
    vn_list = "".join([f"<li>{clean(x)}</li>" for x in data.get('vn_summary', [])])
    biz_list = "".join([f"<li>{clean(x)}</li>" for x in data.get('biz_recommendations', [])])

    # Template HTML chuẩn CIBG
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{ size: A4; margin: 20mm 15mm; @bottom-right {{ content: "Trang " counter(page); font-family: 'Roboto'; font-size: 9pt; }} }}
            body {{ font-family: 'Roboto', sans-serif; font-size: 10.5pt; line-height: 1.6; color: #333; }}
            .logo {{ font-weight: bold; font-size: 16pt; color: #C00000; border: 2px solid #C00000; padding: 5px 10px; display: inline-block; }}
            .banner {{ background-color: #C00000; color: white; padding: 20px; margin: 20px 0; }}
            h2 {{ font-size: 14pt; color: #C00000; border-bottom: 2px solid #C00000; text-transform: uppercase; }}
            h3 {{ font-size: 11pt; font-weight: bold; margin-top: 10px; }}
            ul {{ padding-left: 20px; }}
        </style>
    </head>
    <body>
        <div class="logo">CIBG MARKET ANALYSIS</div>
        <div class="banner">
            <h1 style="margin:0; font-size:18pt;">NHỊP ĐẬP THỊ TRƯỜNG: {data.get('week_number', 'Hàng tuần')}</h1>
            <p style="margin:5px 0 0 0;">Thời gian: {data.get('date_range', today)} | Trạng thái: <b>{data.get('sentiment', '')}</b></p>
        </div>
        <section><h2>A. KINH TẾ THẾ GIỚI</h2><h3>Tiêu điểm: {clean(data.get('world_hot_spot'))}</h3><ul>{world_list}</ul>{regions_html}</section>
        <section><h2>B. KINH TẾ VIỆT NAM</h2><ul>{vn_list}</ul>
            <p><b>Lạm phát:</b> {clean(data.get('vn_growth_inflation'))}</p>
            <p><b>Tỷ giá:</b> {clean(data.get('vn_exchange_rate'))} | <b>Vàng:</b> {clean(data.get('vn_gold'))}</p>
        </section>
        <section><h2>C. HÀM Ý DOANH NGHIỆP</h2><ul>{biz_list}</ul></section>
    </body>
    </html>
    """
    
    pdf = HTML(string=html_content).write_pdf()
    return Response(content=pdf, media_type="application/pdf")
