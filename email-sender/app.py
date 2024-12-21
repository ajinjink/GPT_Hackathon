import streamlit as st
import time
from datetime import datetime
from email_management import email_manage
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

load_dotenv('.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


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

def get_emails(email_manager, useremail, password):
    _, emails_dict = email_manager.fetch_email(useremail, password)
    
    # Transform the emails dictionary into the expected thread format
    threads = []
    for subject, messages in emails_dict.items():
        thread = {
            "thread_id": str(len(threads) + 1),
            "subject": subject,
            "messages": messages
        }
        threads.append(thread)
    
    return threads

def generate_ai_response(thread):
    """
    Generate AI response for an email thread using OpenAI.
    
    Args:
        thread (dict): Email thread containing messages and subject
        
    Returns:
        str: Generated response
    """
    # Initialize ChatOpenAI
    llm = ChatOpenAI(
        temperature=0.7,
        model_name="gpt-4o-mini"
    )
    
    # Create prompt template
    template = """
    당신은 전문적이고 공손한 이메일 응답을 작성하는 비서입니다.
    다음 이메일 스레드를 분석하고 적절한 응답을 작성해주세요.
    
    이메일 제목: {subject}
    
    이전 대화 내역:
    {conversation_history}
    
    마지막 메시지:
    {last_message}
    
    다음 사항을 고려하여 답장을 작성해주세요:
    1. 공손하고 전문적인 톤을 유지하세요
    2. 이전 대화 맥락을 고려하세요
    3. 구체적이고 명확한 답변을 제공하세요
    4. 필요한 경우 추가 질문이나 명확한 설명을 포함하세요
    
    답장:
    """
    
    # Create prompt from template
    prompt = PromptTemplate(
        input_variables=["subject", "conversation_history", "last_message"],
        template=template
    )
    
    # Create chain
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Prepare conversation history
    conversation_history = "\n".join([
        f"From: {msg['from']}\n내용: {msg['content']}\n"
        for msg in thread['messages'][:-1]  # Exclude the last message
    ])
    
    # Get last message
    last_message = thread['messages'][-1]['content']
    
    # Generate response
    response = chain.run({
        "subject": thread['subject'],
        "conversation_history": conversation_history,
        "last_message": last_message
    })
    
    return response.strip()

def safe_generate_ai_response(thread):
    """
    Safely generate AI response with error handling.
    """
    try:
        return generate_ai_response(thread)
    except Exception as e:
        print(f"Error generating AI response: {str(e)}")
        return "죄송합니다. 답장 생성 중 오류가 발생했습니다. 다시 시도해 주세요."

def handle_email_send(thread_idx, thread, email_manager, user, password):
    """이메일 전송 처리를 위한 함수"""
    text_to_send = st.session_state.edited_texts[f"thread_{thread_idx}"]
    
    receiver = thread['messages'][-1]['from']
    subject = thread['subject']
    try:
        email_manager.send_email(user, password, receiver, subject, text_to_send)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def on_text_change(thread_idx):
    key = f"textarea_{thread_idx}"
    if key in st.session_state:
        st.session_state.edited_texts[f"thread_{thread_idx}"] = st.session_state[key]

def main(email_manager, useremail, password):
    st.title("📧 AI 이메일 어시스턴트")
    
    # 세션 상태 초기화
    if 'ai_responses' not in st.session_state:
        st.session_state.ai_responses = {}
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = {}
    if 'edited_texts' not in st.session_state:
        st.session_state.edited_texts = {}
    if 'emails' not in st.session_state:
        st.session_state.emails = get_emails(email_manager, useremail, password)
    if 'expanded_threads' not in st.session_state:
        st.session_state.expanded_threads = set()

    # 메인 화면
    tab1, tab2 = st.tabs(["📥 받은 메일함", "📤 보낸 메일함"])
    
    with tab1:
        st.subheader("받은 메일함")
        for idx, thread in enumerate(st.session_state.emails):
            thread_key = f"expander_{idx}"
            if thread_key not in st.session_state:
                st.session_state[thread_key] = False
            if f"thread_{idx}" in st.session_state.ai_responses or st.session_state.edit_mode.get(idx, False):
                st.session_state[thread_key] = True
                
            with st.expander(f"📨 {thread['subject']} ({len(thread['messages'])}개의 메시지)", expanded=st.session_state[thread_key]):
                # expander가 클릭되었을 때만 상태 변경
                if st.session_state[thread_key]:
                    st.session_state.expanded_threads.add(idx)
                else:
                    st.session_state.expanded_threads.discard(idx)
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
                        
                        # text_area
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

                                success = handle_email_send(idx, thread, email_manager, useremail, password)
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
                            
                            # expander 상태를 유지하면서 수정 모드 전환
                            st.session_state[f"expander_{idx}"] = True
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
    email_a = os.getenv('USER_EMAIL')
    password = os.getenv('PASSWORD')

    email_manager = email_manage()
    main(email_manager, email_a, password)

