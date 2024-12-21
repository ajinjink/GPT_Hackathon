import os
from io import BytesIO

import arxiv
import requests
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")


def search_arxiv(topic):
    """arXiv에서 논문 검색"""
    search = arxiv.Search(
        query=topic, max_results=10, sort_by=arxiv.SortCriterion.Relevance
    )
    return list(search.results())


def extract_pdf_text(pdf_url):
    """PDF URL에서 텍스트 추출"""
    try:
        with st.spinner("PDF 다운로드 중..."):
            response = requests.get(pdf_url)
            response.raise_for_status()

        with st.spinner("텍스트 추출 중..."):
            pdf_file = BytesIO(response.content)
            pdf_reader = PdfReader(pdf_file)

            text = ""
            # max_pages = min(5, len(pdf_reader.pages))
            total_pages = len(pdf_reader.pages)

            progress_text = st.empty()
            progress_bar = st.progress(0)

            for page_num in range(total_pages):
                text += pdf_reader.pages[page_num].extract_text()

                progress = (page_num + 1) / total_pages
                progress_bar.progress(progress)
                progress_text.text(
                    f"진행률: {int(progress * 100)}% ({page_num + 1}/{total_pages} 페이지)"
                )

            cleaned_text = text.replace("\n", " ").strip()
            return cleaned_text

    except Exception as e:
        st.error(f"PDF 처리 중 오류가 발생했습니다: {str(e)}")
        return None


def main():
    st.title("📚 논문 검색 및 PDF 뷰어")

    with st.sidebar:
        st.header("검색 설정")
        topic = st.text_input(
            "검색할 주제를 입력하세요:", placeholder="예: machine learning"
        )
        search_button = st.button("검색")
        should_search = search_button or (
            topic and topic != st.session_state.get("previous_search", "")
        )

        st.markdown("---")
        st.markdown(
            """
        ### 사용 방법
        1. 검색하고 싶은 주제를 입력하세요
        2. 검색 결과에서 관심 있는 논문을 선택하세요
        3. PDF 텍스트 보기를 클릭하면 논문 내용을 볼 수 있습니다
        """
        )

    if should_search and topic:
        st.session_state.previous_search = topic

        with st.spinner("논문을 검색중입니다..."):
            results = search_arxiv(topic)

            if not results:
                st.warning("검색 결과가 없습니다.")
                return

            st.session_state.search_results = results

    # 검색 결과 표시 부분을 수정
    if "search_results" in st.session_state:
        st.header("검색 결과")

        for idx, result in enumerate(st.session_state.search_results):
            # PDF 텍스트 상태를 저장하기 위한 session_state 키 생성
            pdf_key = f"pdf_text_{idx}"

            with st.expander(f"{result.title}"):
                st.markdown(f"### {result.title}")
                st.markdown(
                    f"**저자:** {', '.join([str(author) for author in result.authors])}"
                )
                st.markdown(f"**카테고리:** {result.primary_category}")
                st.markdown(f"**출판일:** {result.published.strftime('%Y-%m-%d')}")
                if result.doi:
                    st.markdown(f"**DOI:** {result.doi}")
                st.markdown("**초록:**")
                st.markdown(result.summary.replace("\n", " "))
                st.markdown(f"[PDF 링크]({result.pdf_url})")

                if st.button("PDF 텍스트 보기", key=f"pdf_{idx}"):
                    pdf_text = extract_pdf_text(result.pdf_url)
                    if pdf_text:
                        st.session_state[pdf_key] = pdf_text

                # 저장된 PDF 텍스트가 있으면 표시
                if pdf_key in st.session_state:
                    st.markdown("### 논문 내용")
                    st.text_area(
                        "",
                        st.session_state[pdf_key],
                        height=300,
                        key=f"text_area_{idx}",
                    )

                    st.download_button(
                        label="텍스트 파일로 다운로드",
                        data=st.session_state[pdf_key],
                        file_name=f"{result.title}.txt",
                        mime="text/plain",
                        key=f"download_{idx}",
                    )


if __name__ == "__main__":
    st.set_page_config(
        page_title="ArXiv Paper Viewer",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    main()
