import streamlit as st
import openai
import time
import json
import os
from typing import List, Dict, Any
from datetime import datetime
import requests

# 페이지 설정
st.set_page_config(
    page_title="의약품 허가심사보고서 AI 챗봇",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 고정된 Assistant ID
FIXED_ASSISTANT_ID = "asst_nPcXHjfN0G8nFcpWPxo08byE"

# CSS 스타일 적용
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #fafafa;
    }
    
    .feature-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stat-box {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .typing-indicator {
        color: #667eea;
        font-style: italic;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

# 환경변수에서 API Key 읽기
api_key = os.getenv("OPENAI_API_KEY")

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>💊 의약품 허가심사보고서 AI 챗봇</h1>
    <p>의약품 관련 질문에 전문적이고 정확한 답변을 제공합니다</p>
</div>
""", unsafe_allow_html=True)

# API 키 확인
if not api_key:
    st.error("⚠️ 환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")
    st.stop()

# OpenAI 클라이언트 초기화
try:
    client = openai.OpenAI(api_key=api_key)
    # API 키 유효성 확인
    models = client.models.list()
except Exception as e:
    st.error(f"❌ OpenAI 클라이언트 초기화 실패: {str(e)}")
    st.stop()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0
if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = datetime.now()

def create_thread() -> str:
    """대화 스레드 생성"""
    try:
        thread = client.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"Thread 생성 실패: {str(e)}")
        return None

def send_message(thread_id: str, message: str) -> str:
    """메시지 전송 및 응답 받기"""
    try:
        # 메시지 추가
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # 실행 시작
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=FIXED_ASSISTANT_ID
        )
        
        # 실행 완료 대기
        with st.spinner("🤖 AI가 답변을 생성하고 있습니다..."):
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                if run_status.status == "completed":
                    break
                elif run_status.status == "failed":
                    st.error(f"❌ 답변 생성 실패: {run_status.last_error}")
                    return None
                elif run_status.status == "requires_action":
                    st.info("🔄 추가 작업이 필요합니다...")
                
                time.sleep(1)
        
        # 메시지 가져오기
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        
        # 텍스트 내용 추출
        content = ""
        for content_item in latest_message.content:
            if content_item.type == "text":
                content += content_item.text.value
        
        return content
        
    except Exception as e:
        st.error(f"❌ 메시지 전송 실패: {str(e)}")
        return None

def get_suggested_questions():
    """자주 묻는 질문 예시"""
    return [
        "이 의약품의 주요 적응증은 무엇인가요?",
        "자료제출의약품 제형변경 사례를 알려주세요.",
        "용법과 용량은 어떻게 되나요?",
        "투여경로 변경 자료제출의약품 사례를 알려주세요",
    ]

# 통계 정보 표시
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💬 총 질문 수", st.session_state.total_questions)
with col2:
    session_duration = datetime.now() - st.session_state.session_start_time
    st.metric("⏱️ 세션 시간", f"{session_duration.seconds // 60}분")
with col3:
    st.metric("🤖 Assistant ID", f"***{FIXED_ASSISTANT_ID[-8:]}")

# 기능 소개
st.markdown("""
<div class="feature-box">
    <h3>🚀 주요 기능</h3>
    <ul>
        <li><strong>즉시 사용 가능</strong>: 별도의 설정 없이 바로 질문 시작</li>
        <li><strong>전문 지식</strong>: 의약품 허가심사보고서 기반 정확한 답변</li>
        <li><strong>대화 기록</strong>: 세션 동안 질문과 답변 기록 유지</li>
        <li><strong>빠른 질문</strong>: 자주 묻는 질문 버튼으로 빠른 접근</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# 자주 묻는 질문 버튼들
st.markdown("### 💡 자주 묻는 질문")
suggested_questions = get_suggested_questions()

# 4개씩 2행으로 배치
col1, col2, col3, col4 = st.columns(4)
cols = [col1, col2, col3, col4]

for i, question in enumerate(suggested_questions):
    with cols[i % 4]:
        if st.button(question, key=f"suggest_{i}", help="클릭하면 자동으로 질문이 입력됩니다"):
            st.session_state.suggested_question = question

# 제안된 질문이 있으면 자동으로 처리
if hasattr(st.session_state, 'suggested_question'):
    suggested_q = st.session_state.suggested_question
    del st.session_state.suggested_question
    
    # Thread 생성 (필요시)
    if not st.session_state.thread_id:
        st.session_state.thread_id = create_thread()
    
    if st.session_state.thread_id:
        # 질문 기록
        st.session_state.messages.append({"role": "user", "content": suggested_q})
        st.session_state.total_questions += 1
        
        # 답변 생성
        response = send_message(st.session_state.thread_id, suggested_q)
        
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})

# 대화 기록 표시
if st.session_state.messages:
    st.markdown("### 💬 대화 기록")
    
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**질문:** {message['content']}")
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"])

# 메시지 입력
st.markdown("### ✍️ 질문하기")
user_input = st.chat_input("의약품 허가심사보고서에 대해 질문해보세요...", key="main_input")

if user_input:
    # Thread 생성 (필요시)
    if not st.session_state.thread_id:
        st.session_state.thread_id = create_thread()
    
    if st.session_state.thread_id:
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.total_questions += 1
        
        # 사용자 메시지 표시
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**질문:** {user_input}")
        
        # AI 응답 생성
        response = send_message(st.session_state.thread_id, user_input)
        
        if response:
            # AI 응답 표시
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(response)
            
            # 응답 기록에 추가
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 페이지 새로고침으로 통계 업데이트
            st.rerun()

# 사이드바 (축소된 상태로 시작)
with st.sidebar:
    st.markdown("### 🔧 설정")
    
    # 대화 초기화
    if st.button("🔄 대화 초기화", help="현재 대화 기록을 모두 삭제합니다"):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.session_state.total_questions = 0
        st.session_state.session_start_time = datetime.now()
        st.success("✅ 대화가 초기화되었습니다!")
        st.rerun()
    
    # 대화 기록 다운로드
    if st.session_state.messages:
        chat_history = ""
        for i, message in enumerate(st.session_state.messages):
            role = "사용자" if message["role"] == "user" else "AI 챗봇"
            chat_history += f"{role}: {message['content']}\n\n"
        
        st.download_button(
            label="💾 대화 기록 다운로드",
            data=chat_history,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="현재 대화 기록을 텍스트 파일로 다운로드합니다"
        )
    
    st.markdown("---")
    st.markdown("### ℹ️ 도움말")
    st.markdown("""
    **사용법:**
    1. 위의 자주 묻는 질문 버튼을 클릭하거나
    2. 아래 입력창에 직접 질문을 입력하세요
    
    **팁:**
    - 구체적인 질문일수록 정확한 답변을 받을 수 있습니다
    - 의약품명, 성분명 등을 명확히 명시해주세요
    - 여러 질문을 한 번에 하기보다는 하나씩 질문해주세요
    """)
    
    st.markdown("---")
    st.markdown("### 📊 세션 정보")
    st.markdown(f"**Assistant ID:** `{FIXED_ASSISTANT_ID[-12:]}`")
    st.markdown(f"**세션 시작:** {st.session_state.session_start_time.strftime('%H:%M:%S')}")
    
    # 시스템 상태
    if st.session_state.thread_id:
        st.success("🟢 챗봇 활성화됨")
    else:
        st.info("⚪ 챗봇 대기중")

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p>💊 의약품 허가심사보고서 AI 챗봇 | 정확하고 신뢰할 수 있는 의약품 정보를 제공합니다</p>
</div>
""", unsafe_allow_html=True)
