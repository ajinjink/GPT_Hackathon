import streamlit as st
import PyPDF2
import json
import base64
import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from openai import OpenAI

class PDFQuestionGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def extract_text_from_range(self, pdf_file, start_page, end_page):
        """PDF에서 지정된 범위의 텍스트를 추출"""
        reader = PdfReader(pdf_file)
        pages = reader.pages
        text = ""
        for page_number in range(start_page - 1, end_page):
            sub = pages[page_number].extract_text()
            text += sub
        return text

    def split_text_to_chunks(self, text, detail_level):
        """텍스트를 청크로 분할"""
        # 상세도에 따른 청크 크기 조정
        detail_mapping = {"하": 1000, "중": 750, "상": 500}
        chunk_size = detail_mapping[detail_level]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        splits = text_splitter.split_text(text)
        return splits

    def create_questions_from_chunk(self, chunk, number_of_questions, feedback='', requirements =''):
        """
        특정 청크에서 문제를 생성합니다.
        - chunk: 텍스트 청크
        - number_of_questions: 생성할 문제 수
        - feedback: 문제에 대한 피드백 (옵션)
        """
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    입력된 내용을 바탕으로 {number_of_questions}개의 문제를 만들어주세요:
                    요구사항 : {requirements}
                    feedback 내용은 다음과 같습니다.
                    {feedback}
                    feedback이 있으면 그것을 참고하여 문제를 만들어주세요.
                    """
                },
                {
                    "role": "user",
                    "content": chunk
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "problems_with_answers",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "questions": {
                                "type": "array",
                                "description": "A collection of questions, where each question is paired with its answer.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {
                                            "type": "string",
                                            "description": "The statement of the question."
                                        },
                                        "answer": {
                                            "type": "string",
                                            "description": "The solution or answer to the question."
                                        }
                                    },
                                    "required": ["question", "answer"],
                                    "additionalProperties": False
                                }
                            },
                            "number_of_problems": {
                                "type": "number",
                                "description": "The total number of questions represented in the questions array."
                            }
                        },
                        "required": ["questions", "number_of_problems"],
                        "additionalProperties": False
                    }
                }
            },
            temperature=0.5,
            max_tokens=16383,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content

def get_download_link(json_data, filename="questions.json"):
    """JSON 데이터를 다운로드 가능한 링크로 변환"""
    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(json_str.encode('utf-8')).decode()
    href = f'data:application/json;charset=utf-8;base64,{b64}'
    return href

def init_session_state():
    """세션 상태 초기화"""
    if 'current_chunk' not in st.session_state:
        st.session_state.current_chunk = 1
    if 'all_questions' not in st.session_state:
        st.session_state.all_questions = []
    if 'generation_started' not in st.session_state:
        st.session_state.generation_started = False
    if 'feedback_applied' not in st.session_state:
        st.session_state.feedback_applied = {}
    if 'text_chunks' not in st.session_state:
        st.session_state.text_chunks = []
    if 'generator' not in st.session_state:
        st.session_state.generator = None

def reset_session():
    """세션 상태 리셋"""
    st.session_state.current_chunk = 1
    st.session_state.all_questions = []
    st.session_state.generation_started = False
    st.session_state.feedback_applied = {}
    st.session_state.text_chunks = []

def main():
    st.title("PDF 문제 생성기")
    
    # 환경 변수 로드
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    # 세션 상태 초기화
    init_session_state()
    
    if not st.session_state.generator:
        st.session_state.generator = PDFQuestionGenerator(api_key=api_key)
    
    # PDF 파일 업로드
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
    
    if uploaded_file:
        # PDF 정보 표시
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        total_pages = len(pdf_reader.pages)
        st.info(f"총 페이지 수: {total_pages}")
        
        # 페이지 범위 선택
        col1, col2 = st.columns(2)
        with col1:
            start_page = st.number_input("시작 페이지", min_value=1, max_value=total_pages, value=1)
        with col2:
            end_page = st.number_input("끝 페이지", min_value=1, max_value=total_pages, value=min(5, total_pages))
        
        # 설정 컨테이너
        with st.container():
            num_questions = st.number_input(
                "생성할 문제 수를 입력하세요",
                min_value=1,
                value=20
            )

            detail_level = st.select_slider(
                "문제 상세도를 선택하세요",
                options=["하", "중", "상"],
                value="중"
            )
            
            requirements = st.text_input("요구사항을 입력하세요", value="문제는 중요한 개념을 다루고 있어야 합니다.")

            st.markdown("---")
            st.markdown("### 모든 설정이 완료되었다면 문제 생성을 시작하세요")

            # 문제 생성 시작
            if not st.session_state.generation_started and st.button("문제 생성 시작"):
                with st.spinner("텍스트를 추출하고 분석 중입니다..."):
                    # 텍스트 추출 및 청크 분할
                    extracted_text = st.session_state.generator.extract_text_from_range(
                        uploaded_file, start_page, end_page
                    )
                    st.session_state.text_chunks = st.session_state.generator.split_text_to_chunks(
                        extracted_text, detail_level
                    )
                    st.session_state.generation_started = True
                    st.rerun()

        # 문제 생성 프로세스
        if st.session_state.generation_started:
            chunk_number = len(st.session_state.text_chunks)
            questions_per_chunk = max(1, num_questions // chunk_number)
            
            st.subheader(f"청크 {st.session_state.current_chunk}/{chunk_number} 문제 생성")
            progress = st.progress(st.session_state.current_chunk / chunk_number)
            st.markdown("---")
            
            with st.spinner("문제를 생성하는 중입니다..."):
                # 현재 청크에 대한 피드백 가져오기
                feedback = st.session_state.feedback_applied.get(
                    str(st.session_state.current_chunk), None
                )
                
                # 현재 청크의 문제 생성
                current_chunk = st.session_state.text_chunks[st.session_state.current_chunk - 1]
                questions_response = st.session_state.generator.create_questions_from_chunk(
                    current_chunk, questions_per_chunk, feedback, requirements
                )
                questions_response = json.loads(questions_response)
                current_questions = questions_response["questions"]
                
                st.success(f"{len(current_questions)}개의 문제가 생성되었습니다!")
                
                # 생성된 문제 표시
                with st.expander("생성된 문제 미리보기", expanded=True):
                    for i, q in enumerate(current_questions, 1):
                        st.markdown(f"**문제 {i}**")
                        st.write(f"Q: {q['question']}")
                        st.write(f"A: {q['answer']}")
                        st.divider()
                
                # 피드백 입력 및 재생성
                col1, col2 = st.columns([3, 1])
                with col1:
                    feedback = st.text_area(
                        "문제에 대한 피드백을 입력해주세요",
                        key=f'feedback_{st.session_state.current_chunk}',
                        help="피드백을 입력하고 재생성 버튼을 누르면 피드백을 반영한 새로운 문제가 생성됩니다."
                    )
                with col2:
                    if st.button("현재 청크 재생성"):
                        if feedback:
                            st.session_state.feedback_applied[str(st.session_state.current_chunk)] = feedback
                            st.rerun()
                
                st.markdown("---")
                
                # 다음 청크로 이동 또는 완료
                st.info("👉 현재 청크의 문제가 마음에 들면 '완료' 버튼을 눌러 다음 청크로 넘어가세요.")
                if st.button(f"청크 {st.session_state.current_chunk} 완료"):
                    st.session_state.all_questions.extend(current_questions)
                    
                    if st.session_state.current_chunk < chunk_number:
                        st.session_state.current_chunk += 1
                        st.rerun()
                    else:
                        st.success("모든 청크의 문제 생성이 완료되었습니다!")
                        
                        # 최종 다운로드 링크
                        download_link = get_download_link(st.session_state.all_questions)
                        st.markdown(
                            f'<a href="{download_link}" download="questions.json">전체 문제 JSON 파일 다운로드</a>',
                            unsafe_allow_html=True
                        )
                        
                        # 새로운 생성 시작
                        if st.button("새로운 문제 생성 시작"):
                            reset_session()
                            st.rerun()

if __name__ == "__main__":
    main()