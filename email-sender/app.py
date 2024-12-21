import streamlit as st
import time
from datetime import datetime

# CSS 스타일 정의
st.markdown("""
<style>
    .sent-message {
        background-color: #e5ffe7;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .received-message {
        background-color: #E3F2FD;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .ai-message {
        background-color: #F0F4C3;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        border-left: 4px solid #9E9D24;
    }
    .edit-mode {
        border: 2px solid #FFB74D;
        padding: 10px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 더미 이메일 데이터 - 스레드 포함
initial_emails = [
    {
        "thread_id": "1",
        "subject": "제품 문의",
        "messages": [
            {
                "from": "client@example.com",
                "to": "user@example.com",
                "content": "안녕하세요, 귀사의 제품 A와 B에 대해 궁금한 점이 있습니다.",
                "timestamp": "2024-12-20 09:30",
                "type": "received"
            },
            {
                "from": "user@example.com",
                "to": "client@example.com",
                "content": "안녕하세요, 어떤 점이 궁금하신지 말씀해 주시면 감사하겠습니다.",
                "timestamp": "2024-12-20 10:15",
                "type": "sent"
            },
            {
                "from": "client@example.com",
                "to": "user@example.com",
                "content": "제품 A의 가격과 B의 배송 기간이 궁금합니다.",
                "timestamp": "2024-12-21 09:30",
                "type": "received"
            }
        ]
    },
    {
        "thread_id": "2",
        "subject": "미팅 일정 조율",
        "messages": [
            {
                "from": "partner@example.com",
                "to": "user@example.com",
                "content": "다음 주 미팅 일정 조율을 위해 연락드립니다.",
                "timestamp": "2024-12-20 14:30",
                "type": "received"
            },
            {
                "from": "user@example.com",
                "to": "partner@example.com",
                "content": "네, 다음 주 월요일 오후는 어떠신가요?",
                "timestamp": "2024-12-20 15:45",
                "type": "sent"
            },
            {
                "from": "partner@example.com",
                "to": "user@example.com",
                "content": "죄송하지만 월요일은 다른 일정이 있습니다. 화요일이나 수요일은 가능할까요?",
                "timestamp": "2024-12-21 10:15",
                "type": "received"
            }
        ]
    }
]

# AI 답장 생성 더미 함수
def generate_ai_response(thread):
    time.sleep(1)  # AI 처리 시간 시뮬레이션
    last_message = thread["messages"][-1]["content"]
    responses = {
        "제품 A의 가격과 B의 배송 기간이 궁금합니다.": 
            "제품 A의 가격은 99,000원이며, 제품 B는 현재 7일 이내 배송이 가능합니다. 추가로 궁금하신 점이 있으시다면 말씀해 주세요.",
        "죄송하지만 월요일은 다른 일정이 있습니다. 화요일이나 수요일은 가능할까요?":
            "네, 화요일 오후 2시에 미팅을 진행하면 좋을 것 같습니다. 가능하신가요?"
    }
    return responses.get(last_message, "죄송합니다. 요청하신 내용을 처리할 수 없습니다.")

# 이메일 전송 더미 함수
def send_email(to_address, content):
    time.sleep(1)  # 전송 시간 시뮬레이션
    print("send: :", content)
    return True

def handle_email_send(thread_idx, thread):
    """이메일 전송 처리를 위한 함수"""
    text_to_send = st.session_state.edited_texts[f"thread_{thread_idx}"]
    success = send_email(thread['messages'][-1]['from'], text_to_send)
    if success:
        # 상태 초기화를 위한 플래그 설정
        st.session_state[f"email_sent_{thread_idx}"] = True
        st.rerun()

def on_text_change(thread_idx):
    key = f"textarea_{thread_idx}"
    if key in st.session_state:
        st.session_state.edited_texts[f"thread_{thread_idx}"] = st.session_state[key]
        print(f"텍스트 변경됨: {st.session_state[key]}")  # 디버깅용

def main():
    st.title("📧 AI 이메일 어시스턴트")
    
    # 세션 상태 초기화
    if 'ai_responses' not in st.session_state:
        st.session_state.ai_responses = {}
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = {}
    if 'edited_texts' not in st.session_state:
        st.session_state.edited_texts = {}
    if 'emails' not in st.session_state:
        st.session_state.emails = initial_emails
    
    # 사이드바에 이메일 계정 정보
    with st.sidebar:
        st.header("계정 정보")
        email = st.text_input("이메일 주소", value="user@example.com")
        password = st.text_input("비밀번호", type="password", value="dummy_password")
        if st.button("로그인"):
            st.success("로그인 되었습니다!")

    # 메인 화면
    tab1, tab2 = st.tabs(["📥 받은 메일함", "📤 보낸 메일함"])
    
    with tab1:
        st.subheader("받은 메일함")
        for idx, thread in enumerate(st.session_state.emails):
            with st.expander(f"📨 {thread['subject']} ({len(thread['messages'])}개의 메시지)"):
                # 이메일 스레드 표시
                for message in thread['messages']:
                    css_class = "sent-message" if message['type'] == 'sent' else "received-message"
                    icon = "📤" if message['type'] == 'sent' else "📥"
                    
                    st.markdown(f"""
                    <div class="{css_class}">
                        {icon} <strong>From:</strong> {message['from']}<br>
                        <strong>To:</strong> {message['to']}<br>
                        <strong>시간:</strong> {message['timestamp']}<br>
                        <br>
                        {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                
                # AI 답장 생성 버튼
                if f"thread_{idx}" not in st.session_state.ai_responses and st.button("AI 답장 생성", key=f"generate_{idx}"):
                    with st.spinner("AI가 답장을 생성중입니다..."):
                        response = generate_ai_response(thread)
                        st.session_state.ai_responses[f"thread_{idx}"] = response
                        st.session_state.edited_texts[f"thread_{idx}"] = response
                
                # AI 답장이 생성된 경우 표시
                if f"thread_{idx}" in st.session_state.ai_responses:
                    if not st.session_state.edit_mode.get(idx, False):
                        # AI 생성 답장 표시
                        st.markdown(f"""
                        <div class="ai-message">
                            🤖 <strong>AI 추천 답장:</strong><br>
                            <br>
                            {st.session_state.edited_texts.get(f"thread_{idx}", st.session_state.ai_responses[f"thread_{idx}"])}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # 수정 모드 UI
                        st.markdown('<div class="edit-mode">', unsafe_allow_html=True)
                        st.write("✏️ 답장 수정 모드")
                        
                        # 초기값 설정
                        if f"textarea_{idx}" not in st.session_state:
                            st.session_state[f"textarea_{idx}"] = st.session_state.edited_texts.get(
                                f"thread_{idx}", 
                                st.session_state.ai_responses[f"thread_{idx}"]
                            )
                        
                        # text_area with callback
                        st.text_area(
                            "답장을 수정해주세요",
                            key=f"textarea_{idx}",
                            on_change=on_text_change,
                            args=(idx,),
                            height=200
                        )
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    
                    # 버튼들
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("답장 전송", key=f"send_{idx}"):
                            with st.spinner("답장을 전송중입니다..."):
                                text_to_send = st.session_state.edited_texts.get(
                                    f"thread_{idx}", 
                                    st.session_state.ai_responses[f"thread_{idx}"]
                                )

                                success = send_email(thread['messages'][-1]['from'], text_to_send)
                                if success:
                                    # 메시지를 스레드에 추가
                                    new_message = {
                                        "from": "user@example.com",
                                        "to": thread['messages'][-1]['from'],
                                        "content": text_to_send,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "type": "sent"
                                    }
                                    st.session_state.emails[idx]['messages'].append(new_message)
                                    
                                    # # 상태 초기화
                                    del st.session_state.ai_responses[f"thread_{idx}"]
                                    st.session_state.edit_mode[idx] = False
                                    if f"textarea_{idx}" in st.session_state:
                                        del st.session_state[f"textarea_{idx}"]
                                    if f"thread_{idx}" in st.session_state.edited_texts:
                                        del st.session_state.edited_texts[f"thread_{idx}"]
                                    
                                    st.success("성공적으로 전송되었습니다!")
                                    time.sleep(2)
                                    st.rerun()
                        
                    with col2:
                        if st.button("다시 생성", key=f"regenerate_{idx}"):
                            with st.spinner("AI가 답장을 다시 생성중입니다..."):
                                # 새로운 AI 답장 생성
                                new_response = generate_ai_response(thread)
                                st.session_state.ai_responses[f"thread_{idx}"] = new_response
                                st.session_state.edited_texts[f"thread_{idx}"] = new_response
                                # 수정 모드였다면 초기화
                                st.session_state.edit_mode[idx] = False
                                if f"textarea_{idx}" in st.session_state:
                                    del st.session_state[f"textarea_{idx}"]
                                st.rerun()
                    with col3:
                        edit_button_text = "수정 완료" if st.session_state.edit_mode.get(idx, False) else "수정하기"
                        if st.button(edit_button_text, key=f"edit_{idx}"):
                            current_edit_mode = st.session_state.edit_mode.get(idx, False)
                            if current_edit_mode:  # 수정 완료 버튼을 누른 경우
                                # edited_texts에 최종 수정본 저장
                                if f"textarea_{idx}" in st.session_state:
                                    st.session_state.edited_texts[f"thread_{idx}"] = st.session_state[f"textarea_{idx}"]
                            else:  # 수정 시작
                                if f"thread_{idx}" not in st.session_state.edited_texts:
                                    st.session_state.edited_texts[f"thread_{idx}"] = st.session_state.ai_responses[f"thread_{idx}"]
                            
                            st.session_state.edit_mode[idx] = not current_edit_mode
                            st.rerun()
    
    with tab2:
        st.subheader("보낸 메일함")
        # 보낸 메일 표시
        sent_count = 0
        for thread in st.session_state.emails:
            sent_messages = [msg for msg in thread['messages'] if msg['type'] == 'sent']
            sent_count += len(sent_messages)
            
            for message in sent_messages:
                st.markdown(f"""
                <div class="sent-message">
                    📤 <strong>To:</strong> {message['to']}<br>
                    <strong>시간:</strong> {message['timestamp']}<br>
                    <strong>제목:</strong> {thread['subject']}<br>
                    <br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
        
        if sent_count == 0:
            st.info("아직 보낸 메일이 없습니다.")

if __name__ == "__main__":
    main()