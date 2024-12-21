# import streamlit as st
# import PyPDF2
# import json
# import io
# # from langchain_openai import ChatOpenAI
# # from langchain.text_splitter import RecursiveCharacterTextSplitter
# # from langchain.prompts import PromptTemplate
# import base64


# # def extract_text_from_pdf(pdf_file, start_page, end_page):
# #     # pdf_reader = PyPDF2.PdfReader(pdf_file)
# #     # text = ""
    
# #     # # Validate page range
# #     # max_pages = len(pdf_reader.pages)
# #     # start_page = max(1, min(start_page, max_pages))
# #     # end_page = max(start_page, min(end_page, max_pages))
    
# #     # # Extract text from specified pages
# #     # for page_num in range(start_page - 1, end_page):
# #     #     text += pdf_reader.pages[page_num].extract_text()

# #     text = "dummy text"
    
# #     return text

# # def split_text(text, chunk_size=1000):
# #     text_splitter = RecursiveCharacterTextSplitter(
# #         chunk_size=chunk_size,
# #         chunk_overlap=200,
# #         separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
# #     )
# #     return text_splitter.split_text(text)

# def generate_questions(chunk_number, detail_level, feedback=None):
#     print(feedback)
#     if feedback:
#         questions = {"problems":[
#         {"problem":"Explain the concept of 'residual claim' in the context of common stock ownership in a corporation.","answer":"Residual claim refers to the right of shareholders to the remaining assets and earnings of a company after all debts, liabilities, and obligations to creditors have been fulfilled. This means that shareholders are last in line during any liquidation or payout scenarios, but they have the potential to benefit from any remaining profits or assets."},{"problem":"Identify and explain two potential advantages of holding common stock.","answer":"1. **Potential for Capital Gains:** Since common stock represents ownership in a company, shareholders may benefit from the appreciation in the stock's value over time. If the company's value increases, the stock price typically follows, allowing shareholders to sell their shares for a profit.\n2. **Dividend Income:** Many companies distribute a portion of their profits to common shareholders in the form of dividends. This provides an income stream to investors in addition to any capital gains realized."},{"problem":"What are the risks associated with investing in common stock?","answer":"Investing in common stock carries inherent risks, including:\n1. **Market Volatility:** Stock prices can fluctuate widely due to various factors, including economic conditions, market sentiment, and company performance, leading to potential loss of investment value.\n2. **Residual Claim Risk:** In the event of bankruptcy, common shareholders are at risk of losing their entire investment as they are last in line to receive any remaining assets, following bondholders and preferred shareholders."},{"problem":"Discuss how dividend policy can impact the value of a common stock.","answer":"Dividend policy can significantly impact a stock's value through the following channels:\n1. **Signaling Effect:** A stable or increasing dividend can signal a company’s strong financial health and future prospects, potentially boosting stock value.\n2. **Investor Preference:** Some investors prefer regular income through dividends, increasing demand for dividend-paying stocks, which can drive up their price.\n3. **Retention vs. Distribution:** Retaining earnings to reinvest in growth opportunities can lead to increased future profitability, potentially enhancing long-term stock value."},{"problem":"Describe the impact of stock splits and reverse stock splits on common stockholders.","answer":"- **Stock Split:** This involves dividing existing shares into multiple shares. For example, a 2-for-1 stock split doubles the number of shares while halving the share price. It does not affect the overall market capitalization but can enhance liquidity and make shares seem more affordable.\n- **Reverse Stock Split:** This consolidates multiple shares into fewer shares. For instance, a 1-for-2 reverse split halves the number of shares, doubling the share price. While it doesn’t change the market cap, it can improve a company's stock price by reducing the number of shares."}],"number_of_problems":5}
#     else:
#         questions = {"problems":[
#         {"problem":"Explain the concept of 'residual claim' in the context of common stock ownership in a corporation.",
#          "answer":"Residual claim refers to the right of shareholders to the remaining assets and earnings of a company after all debts, liabilities, and obligations to creditors have been fulfilled."},
#         {"problem":"Identify and explain two potential advantages of holding common stock.",
#          "answer":"1. Potential for Capital Gains: Shareholders benefit from stock price appreciation\n2. Dividend Income: Regular distributions of company profits"}]}
#     return questions["problems"]

# def get_download_link(json_data, filename="questions.json"):
#     json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
#     b64 = base64.b64encode(json_str.encode('utf-8')).decode()
#     href = f'data:application/json;charset=utf-8;base64,{b64}'
#     return href

# def init_session_state():
#     if 'current_chunk' not in st.session_state:
#         st.session_state.current_chunk = 1
#     if 'all_questions' not in st.session_state:
#         st.session_state.all_questions = []
#     if 'generation_started' not in st.session_state:
#         st.session_state.generation_started = False
#     if 'feedback_applied' not in st.session_state:
#         st.session_state.feedback_applied = {}


# def reset_session():
#     st.session_state.current_chunk = 1
#     st.session_state.all_questions = []
#     st.session_state.generation_started = False
#     st.session_state.feedback_applied = {}

# def main():
#     st.title("PDF 문제 생성기")
#     init_session_state()
    
#     # PDF 파일 업로드
#     uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
    
#     if uploaded_file:
#         # PDF 정보 표시
#         pdf_reader = PyPDF2.PdfReader(uploaded_file)
#         total_pages = len(pdf_reader.pages)
#         st.info(f"총 페이지 수: {total_pages}")
        
#         # 페이지 범위 선택
#         col1, col2 = st.columns(2)
#         with col1:
#             start_page = st.number_input("시작 페이지", min_value=1, max_value=total_pages, value=1)
#         with col2:
#             end_page = st.number_input("끝 페이지", min_value=1, max_value=total_pages, value=min(5, total_pages))
        
#         with st.container():
#             num_questions = st.number_input(
#                 "생성할 문제 수를 입력하세요",
#                 min_value=1        
#             )

#             # 문제 상세도 선택
#             detail_level = st.select_slider(
#                 "문제 상세도를 선택하세요",
#                 options=["하", "중", "상"],
#                 value="중"
#             )

#             st.markdown("---")
#             st.markdown("### 모든 설정이 완료되었다면 문제 생성을 시작하세요")

#          # 문제 생성 시작 버튼
#         if not st.session_state.generation_started and st.button("문제 생성 시작"):
#             st.session_state.generation_started = True
#             reset_session()
#             st.rerun()

#         # 문제 생성 프로세스
#         if st.session_state.generation_started:
#             chunk_number = 3  # 총 청크 수
            
#             st.subheader(f"청크 {st.session_state.current_chunk}/{chunk_number} 문제 생성")
#             progress = st.progress(st.session_state.current_chunk / chunk_number)
#             st.markdown("---")
            
#             with st.spinner("문제를 생성하는 중입니다..."):
#                 # 이전 피드백이 있으면 가져오기
#                 feedback = st.session_state.get(f'feedback_{st.session_state.current_chunk-1}', None)
                
#                 # 현재 청크의 문제 생성
#                 current_questions = generate_questions(st.session_state.current_chunk, detail_level, feedback)
                
#                 # 문제 표시
#                 st.success(f"{len(current_questions)}개의 문제가 생성되었습니다!")
                
#                 with st.expander("생성된 문제 미리보기", expanded=True):
#                     for i, q in enumerate(current_questions, 1):
#                         st.markdown(f"**문제 {i}**")
#                         st.write(f"Q: {q['problem']}")
#                         st.write(f"A: {q['answer']}")
#                         st.divider()
                
#                 # # 피드백 입력
#                 # feedback = st.text_area(
#                 #     "생성된 문제에 대한 피드백을 입력해주세요 (선택사항)",
#                 #     key=f'feedback_{st.session_state.current_chunk}'
#                 # )
#                 # 피드백 및 재생성
#                 col1, col2 = st.columns([3, 1])
#                 with col1:
#                     feedback = st.text_area(
#                         "문제에 대한 피드백을 입력해주세요",
#                         key=f'feedback_{st.session_state.current_chunk}',
#                         help="피드백을 입력하고 재생성 버튼을 누르면 피드백을 반영한 새로운 문제가 생성됩니다."
#                     )
#                 with col2:
#                     if st.button("현재 청크 재생성", 
#                                help="입력한 피드백을 반영하여 현재 청크의 문제를 다시 생성합니다"):
#                         if feedback:  # 피드백이 있을 때만 저장
#                             st.session_state.feedback_applied[str(st.session_state.current_chunk)] = feedback
#                             st.rerun()
#                 st.markdown("---")
                
#                 # 다음 청크로 이동 또는 완료 버튼
#                 st.info("👉 현재 청크의 문제가 마음에 들면 '완료' 버튼을 눌러 다음 청크로 넘어가세요.")
#                 if st.button(f"청크 {st.session_state.current_chunk} 완료", help="현재 청크의 문제 생성을 완료하고 다음 청크로 넘어갑니다"):
#                     # 현재 문제들을 전체 문제 리스트에 추가
#                     st.session_state.all_questions.extend(current_questions)
                    
#                     if st.session_state.current_chunk < chunk_number:
#                         st.session_state.current_chunk += 1
#                         st.rerun()
#                     else:
#                         st.success("모든 청크의 문제 생성이 완료되었습니다!")
                        
#                         # 최종 다운로드 버튼
#                         download_link = get_download_link(st.session_state.all_questions)
#                         st.markdown(
#                             f'<a href="{download_link}" download="questions.json">전체 문제 JSON 파일 다운로드</a>',
#                             unsafe_allow_html=True
#                         )
                        
#                         # 새로운 생성 시작 버튼
#                         if st.button("새로운 문제 생성 시작"):
#                             reset_session()
#                             st.rerun()

        
#         # if st.button("문제 생성"):
#         #     with st.spinner("문제를 생성하는 중입니다..."):
#         #         # # PDF에서 텍스트 추출
#         #         # text = extract_text_from_pdf(uploaded_file, start_page, end_page)
                
#         #         # # 텍스트 분할
#         #         # text_chunks = split_text(text)
#         #         chunk_number = 3
                
#         #         # # 문제 생성
#         #         for num in range(1, chunk_number + 1):
#         #             questions = generate_questions(chunk_number, detail_level)
                
#         #         # # 결과 표시
#         #             st.success(f"{len(questions)}개의 문제가 생성되었습니다!")
                
#         #         # # 문제 미리보기
#         #             with st.expander("생성된 문제 미리보기"):
#         #                 for i, q in enumerate(questions, 1):
#         #                     st.markdown(f"**문제 {i}**")
#         #                     st.write(f"Q: {q['problem']}")
#         #                     st.write(f"A: {q['answer']}")
#         #                     st.divider()
                
#         #         # 다운로드 버튼
#         #         download_link = get_download_link(questions)
#         #         st.markdown(f'<a href="{download_link}" download="questions.json">문제 JSON 파일 다운로드</a>', unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()



import streamlit as st
import PyPDF2
import json
import io
import base64

def generate_questions(chunk_number, detail_level, feedback=None):
    print(feedback)
    if feedback:
        questions = {"problems":[
        {"problem":"Explain the concept of 'residual claim' in the context of common stock ownership in a corporation.","answer":"Residual claim refers to the right of shareholders to the remaining assets and earnings of a company after all debts, liabilities, and obligations to creditors have been fulfilled. This means that shareholders are last in line during any liquidation or payout scenarios, but they have the potential to benefit from any remaining profits or assets."},{"problem":"Identify and explain two potential advantages of holding common stock.","answer":"1. **Potential for Capital Gains:** Since common stock represents ownership in a company, shareholders may benefit from the appreciation in the stock's value over time. If the company's value increases, the stock price typically follows, allowing shareholders to sell their shares for a profit.\n2. **Dividend Income:** Many companies distribute a portion of their profits to common shareholders in the form of dividends. This provides an income stream to investors in addition to any capital gains realized."}]}
    else:
        questions = {"problems":[
        {"problem":"Explain the concept of 'residual claim' in the context of common stock ownership in a corporation.",
         "answer":"Residual claim refers to the right of shareholders to the remaining assets and earnings of a company after all debts, liabilities, and obligations to creditors have been fulfilled."},
        {"problem":"Identify and explain two potential advantages of holding common stock.",
         "answer":"1. Potential for Capital Gains: Shareholders benefit from stock price appreciation\n2. Dividend Income: Regular distributions of company profits"}]}
    return questions["problems"]

def get_download_link(json_data, filename="questions.json"):
    json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(json_str.encode('utf-8')).decode()
    href = f'data:application/json;charset=utf-8;base64,{b64}'
    return href

def init_session_state():
    if 'current_chunk' not in st.session_state:
        st.session_state.current_chunk = 1
    if 'all_questions' not in st.session_state:
        st.session_state.all_questions = []
    if 'generation_started' not in st.session_state:
        st.session_state.generation_started = False
    if 'feedback_applied' not in st.session_state:
        st.session_state.feedback_applied = {}

def reset_session():
    st.session_state.current_chunk = 1
    st.session_state.all_questions = []
    st.session_state.generation_started = False
    st.session_state.feedback_applied = {}

def main():
    st.title("PDF 문제 생성기")
    init_session_state()
    
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
                min_value=1        
            )

            detail_level = st.select_slider(
                "문제 상세도를 선택하세요",
                options=["하", "중", "상"],
                value="중"
            )

            st.markdown("---")
            st.markdown("### 모든 설정이 완료되었다면 문제 생성을 시작하세요")

            # 문제 생성 시작 버튼
            if not st.session_state.generation_started:
                if st.button("문제 생성 시작"):
                    st.session_state.generation_started = True
                    st.rerun()

        # 문제 생성 프로세스
        if st.session_state.generation_started:
            chunk_number = 3
            
            st.subheader(f"청크 {st.session_state.current_chunk}/{chunk_number} 문제 생성")
            progress = st.progress(st.session_state.current_chunk / chunk_number)
            st.markdown("---")
            
            with st.spinner("문제를 생성하는 중입니다..."):
                feedback = st.session_state.feedback_applied.get(str(st.session_state.current_chunk), None)
                current_questions = generate_questions(st.session_state.current_chunk, detail_level, feedback)
                
                st.success(f"{len(current_questions)}개의 문제가 생성되었습니다!")
                
                with st.expander("생성된 문제 미리보기", expanded=True):
                    for i, q in enumerate(current_questions, 1):
                        st.markdown(f"**문제 {i}**")
                        st.write(f"Q: {q['problem']}")
                        st.write(f"A: {q['answer']}")
                        st.divider()
                
                # 피드백 및 재생성
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
                        
                        download_link = get_download_link(st.session_state.all_questions)
                        st.markdown(
                            f'<a href="{download_link}" download="questions.json">전체 문제 JSON 파일 다운로드</a>',
                            unsafe_allow_html=True
                        )
                        
                        if st.button("새로운 문제 생성 시작"):
                            reset_session()
                            st.rerun()

if __name__ == "__main__":
    main()
