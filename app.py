import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import os

# 1. 페이지 기본 설정
st.set_page_config(page_title="Gemini HTML Generator", layout="wide")

st.title("Gemini 채팅링크 html 변환기 🛠️")
st.markdown("""
Gemini의 공유 링크를 입력하면 **기능(수정, 크기조절, 저장)이 내장된 HTML 파일**로 변환해줍니다.
""")

# 2. URL 입력 받기
default_url = "https://gemini.google.com/share/xxxxx"
url = st.text_input("Gemini 공유 링크 입력:")

# 3. Selenium을 이용한 크롤링 함수 (버전 충돌 해결 버전)
def get_ai_text_content(target_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # 서비스 객체 초기화 변수
    service = None

    # [핵심 수정] 환경에 따른 드라이버 및 브라우저 경로 설정
    # Streamlit Cloud (Linux) 환경
    if os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
        # 리눅스에서는 webdriver_manager를 쓰지 않고 시스템에 설치된 드라이버를 직접 사용
        # 이렇게 해야 브라우저(142)와 드라이버(142) 버전이 정확히 일치함
        if os.path.exists("/usr/bin/chromedriver"):
            service = Service(executable_path="/usr/bin/chromedriver")
        else:
            # 만약 시스템 드라이버가 없으면(혹시 모르니) 다운로드 시도
            service = Service(ChromeDriverManager().install())
            
    # 로컬 (Windows/Mac) 환경
    else:
        # 로컬에서는 webdriver_manager가 알아서 설치
        service = Service(ChromeDriverManager().install())

    try:
        # 드라이버 실행
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        with st.spinner('AI 답변을 분석하고 텍스트를 추출 중입니다... (약 5~10초 소요)'):
            driver.get(target_url)
            time.sleep(6) 
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 불필요한 요소 제거
            for tag in soup.find_all(['img', 'svg', 'video', 'figure', 'picture']):
                tag.decompose()

            for script in soup(["script", "style", "noscript", "iframe"]):
                script.extract()

            # 내용 추출
            content_blocks = soup.find_all(class_="markdown")
            if not content_blocks:
                content_blocks = soup.find_all(['p', 'pre', 'code', 'ul', 'ol', 'h3', 'h4'])

            # 내용 조립
            body_content = ""
            for block in content_blocks:
                if len(block.get_text(strip=True)) < 2:
                    continue
                if hasattr(block, 'attrs'):
                    block.attrs = {} 
                body_content += str(block) + "<br><br>"
            
            if not body_content:
                return None, "내용을 찾을 수 없습니다. 링크가 유효한지 확인해주세요."

            return body_content, None
            
    except Exception as e:
        return None, str(e)
    finally:
        if 'driver' in locals():
            driver.quit()

# 4. 스마트 HTML 생성 함수
def create_smart_html(content):
    """
    수정, 크기 조절, 폭 조절, 파일명 지정 저장이 가능한 HTML 템플릿 생성
    """
    html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Gemini Document</title>
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Pretendard', sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding-bottom: 50px;
            overflow-x: hidden; 
        }}
        #toolbar {{
            position: relative; 
            top: 0; left: 0; width: 100%;
            background: #ffffff;
            border-bottom: 1px solid #ddd;
            padding: 10px 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            z-index: 1000;
            display: flex; align-items: center; justify-content: center;
            gap: 20px; flex-wrap: wrap;
        }}
        .tool-group {{ display: flex; align-items: center; gap: 8px; font-size: 14px; color: #555; }}
        input[type="range"] {{ cursor: pointer; width: 100px; }}
        input[type="text"] {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; width: 150px; }}
        button {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; transition: 0.2s; }}
        #editBtn {{ background-color: #eee; color: #333; }}
        #editBtn:hover {{ background-color: #ddd; }}
        #saveBtn {{ background-color: #2196F3; color: white; }}
        #saveBtn:hover {{ background-color: #1976D2; }}
        #content-container {{
            background-color: white; margin: 0 auto; padding: 40px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.05); border-radius: 8px;
            max-width: 800px; width: 100%;
            font-size: 16px; line-height: 1.7; color: #333;
            word-break: break-word; overflow-wrap: break-word;
        }}
        .editable-mode {{ outline: 2px dashed #2196F3; background-color: #fffdf5 !important; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 6px; overflow-x: auto; font-family: 'D2Coding', monospace; border: 1px solid #eee; white-space: pre; }}
        img, video {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <div id="toolbar">
        <div class="tool-group"><span>📝 편집:</span><button id="editBtn" onclick="toggleEdit()">수정 모드 켜기</button></div>
        <div class="tool-group" style="border-left: 1px solid #ddd; padding-left: 20px;"><span>🔍 글자 크기:</span><input type="range" min="12" max="30" value="16" oninput="adjustFontSize(this.value)"></div>
        <div class="tool-group"><span>↔️ 가로 폭:</span><input type="range" min="400" max="1600" value="800" step="50" oninput="adjustWidth(this.value)"></div>
        <div class="tool-group" style="border-left: 1px solid #ddd; padding-left: 20px;"><input type="text" id="filenameInput" placeholder="파일명"><span style="font-weight:bold;">.html</span><button id="saveBtn" onclick="saveFile()">저장하기</button></div>
    </div>
    <div id="content-container">{content}</div>
    <script>
        const contentContainer = document.getElementById('content-container');
        const editBtn = document.getElementById('editBtn');
        let isEditing = false;
        function adjustFontSize(size) {{ contentContainer.style.fontSize = size + 'px'; }}
        function adjustWidth(width) {{ contentContainer.style.maxWidth = width + 'px'; }}
        function toggleEdit() {{
            if (!isEditing) {{
                contentContainer.contentEditable = "true"; contentContainer.classList.add('editable-mode'); contentContainer.focus();
                editBtn.innerText = "수정 모드 끄기"; editBtn.style.backgroundColor = "#ffcdd2"; isEditing = true;
            }} else {{
                contentContainer.contentEditable = "false"; contentContainer.classList.remove('editable-mode');
                editBtn.innerText = "수정 모드 켜기"; editBtn.style.backgroundColor = "#eee"; isEditing = false;
            }}
        }}
        function saveFile() {{
            if (isEditing) toggleEdit();
            let filename = document.getElementById('filenameInput').value.trim();
            if (!filename) {{ filename = "gemini_saved_" + new Date().getTime(); }}
            if (!filename.endsWith('.html')) {{ filename += ".html"; }}
            const htmlContent = "<!DOCTYPE html>" + document.documentElement.outerHTML;
            const blob = new Blob([htmlContent], {{ type: "text/html" }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url; a.download = filename; document.body.appendChild(a); a.click();
            document.body.removeChild(a); URL.revokeObjectURL(url);
            alert("'" + filename + "' 파일로 저장되었습니다!");
        }}
    </script>
</body>
</html>
    """
    return html_template

# 5. 메인 실행 로직
if st.button("HTML 파일 생성하기 🚀"):
    if not url or "gemini.google.com" not in url:
        st.warning("올바른 Gemini 공유 링크를 입력해주세요.")
    else:
        extracted_text, error = get_ai_text_content(url)
        
        if error:
            st.error(f"오류 발생: {error}")
            st.info("Streamlit Cloud 환경 설정 문제일 수 있습니다. (packages.txt 확인 필요)")
        else:
            final_html = create_smart_html(extracted_text)
            st.success("생성 완료! 아래 버튼을 눌러 다운로드하세요.")
            st.download_button(
                label="📥 HTML 파일 다운로드",
                data=final_html,
                file_name="gemini_smart_doc.html",
                mime="text/html"
            )

