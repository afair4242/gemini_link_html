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
url = st.text_input("Gemini 공유 링크 입력:", value=default_url)

# 3. Selenium을 이용한 크롤링 함수 (클라우드/로컬 호환)
def get_ai_text_content(target_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # [핵심] Streamlit Cloud (Linux) 환경 대응
    # 리눅스 환경에서는 크롬 바이너리 위치를 명시해줘야 안정적으로 동작합니다.
    if os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/chromium-browser"):
        chrome_options.binary_location = "/usr/bin/chromium-browser"

    try:
        # 드라이버 설치 및 실행
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        with st.spinner('AI 답변을 분석하고 텍스트를 추출 중입니다... (약 5~10초 소요)'):
            driver.get(target_url)
            time.sleep(6) # 페이지 로딩 대기 (넉넉하게 설정)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            
            # 불필요한 요소 제거 (이미지, 스크립트 등)
            for tag in soup.find_all(['img', 'svg', 'video', 'figure', 'picture']):
                tag.decompose()

            for script in soup(["script", "style", "noscript", "iframe"]):
                script.extract()

            # Gemini 답변 본문 추출
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
        # 드라이버 종료 (에러가 나더라도 실행)
        if 'driver' in locals():
            driver.quit()

# 4. 스마트 HTML 생성 함수
def create_smart_html(content):
    """
    수정, 크기 조절, 폭 조절, 파일명 지정 저장이 가능한 HTML 템플릿 생성
    (가로 스크롤 방지, 줄바꿈 처리, 툴바 스크롤 고정 해제 완료)
    """
    html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Gemini Document</title>
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

        /* [Box Sizing 초기화] 패딩이 너비에 포함되도록 설정 */
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
            background-color: #f9f9f9;
            margin: 0;
            padding-bottom: 50px;
            /* 전체 화면 가로 스크롤 방지 */
            overflow-x: hidden; 
        }}

        /* 상단 툴바: position relative로 설정하여 스크롤 시 위로 사라짐 */
        #toolbar {{
            position: relative; 
            top: 0;
            left: 0;
            width: 100%;
            background: #ffffff;
            border-bottom: 1px solid #ddd;
            padding: 10px 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .tool-group {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: #555;
        }}

        input[type="range"] {{
            cursor: pointer;
            width: 100px;
        }}
        
        input[type="text"] {{
            padding: 6px 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            width: 150px;
        }}

        button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
            transition: 0.2s;
        }}

        #editBtn {{ background-color: #eee; color: #333; }}
        #editBtn:hover {{ background-color: #ddd; }}
        
        #saveBtn {{ background-color: #2196F3; color: white; }}
        #saveBtn:hover {{ background-color: #1976D2; }}

        /* 메인 컨텐츠 영역 */
        #content-container {{
            background-color: white;
            margin: 0 auto;
            padding: 40px; 
            box-shadow: 0 0 15px rgba(0,0,0,0.05);
            border-radius: 8px;
            
            /* 레이아웃 설정 */
            max-width: 800px;
            width: 100%; /* 화면에 꽉 차게 */
            
            font-size: 16px;
            line-height: 1.7;
            color: #333;
            
            /* 긴 단어 및 URL 줄바꿈 처리 */
            word-break: break-word;
            overflow-wrap: break-word;
        }}

        /* 편집 모드 활성화 시 스타일 */
        .editable-mode {{
            outline: 2px dashed #2196F3;
            background-color: #fffdf5 !important;
        }}

        /* 코드 블록 스타일 */
        pre {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto; /* 코드만 가로 스크롤 허용 */
            font-family: 'D2Coding', monospace;
            border: 1px solid #eee;
            white-space: pre;
        }}
        
        /* 이미지 반응형 처리 */
        img, video {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>

    <div id="toolbar">
        <div class="tool-group">
            <span>📝 편집:</span>
            <button id="editBtn" onclick="toggleEdit()">수정 모드 켜기</button>
        </div>
        
        <div class="tool-group" style="border-left: 1px solid #ddd; padding-left: 20px;">
            <span>🔍 글자 크기:</span>
            <input type="range" min="12" max="30" value="16" oninput="adjustFontSize(this.value)">
        </div>

        <div class="tool-group">
            <span>↔️ 가로 폭:</span>
            <input type="range" min="400" max="1600" value="800" step="50" oninput="adjustWidth(this.value)">
        </div>

        <div class="tool-group" style="border-left: 1px solid #ddd; padding-left: 20px;">
            <input type="text" id="filenameInput" placeholder="파일명 (예: ai_note)">
            <span style="font-weight:bold;">.html</span>
            <button id="saveBtn" onclick="saveFile()">저장하기</button>
        </div>
    </div>

    <div id="content-container">
        {content}
    </div>

    <script>
        const contentContainer = document.getElementById('content-container');
        const editBtn = document.getElementById('editBtn');
        let isEditing = false;

        function adjustFontSize(size) {{
            contentContainer.style.fontSize = size + 'px';
        }}

        function adjustWidth(width) {{
            contentContainer.style.maxWidth = width + 'px';
        }}

        function toggleEdit() {{
            if (!isEditing) {{
                contentContainer.contentEditable = "true";
                contentContainer.classList.add('editable-mode');
                contentContainer.focus();
                editBtn.innerText = "수정 모드 끄기";
                editBtn.style.backgroundColor = "#ffcdd2";
                isEditing = true;
            }} else {{
                contentContainer.contentEditable = "false";
                contentContainer.classList.remove('editable-mode');
                editBtn.innerText = "수정 모드 켜기";
                editBtn.style.backgroundColor = "#eee";
                isEditing = false;
            }}
        }}

        function saveFile() {{
            if (isEditing) toggleEdit();

            let filename = document.getElementById('filenameInput').value.trim();
            if (!filename) {{
                filename = "gemini_saved_" + new Date().getTime();
            }}
            if (!filename.endsWith('.html')) {{
                filename += ".html";
            }}

            const htmlContent = "<!DOCTYPE html>" + document.documentElement.outerHTML;
            const blob = new Blob([htmlContent], {{ type: "text/html" }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
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
            st.info("Streamlit Cloud라면 packages.txt 파일이 있는지 확인해보세요.")
        else:
            final_html = create_smart_html(extracted_text)
            
            st.success("생성 완료! 아래 버튼을 눌러 다운로드하세요.")
            
            st.download_button(
                label="📥 HTML 파일 다운로드",
                data=final_html,
                file_name="gemini_smart_doc.html",
                mime="text/html"
            )
