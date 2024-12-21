import os
from io import BytesIO

import arxiv
import openai
import requests
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


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


def summarize_paper(paper_text):
    """논문 텍스트 요약"""
    # 텍스트 길이 제한 (OpenAI API 토큰 제한 고려)
    max_length = 14000  # 약 4000 토큰
    truncated_text = paper_text[:max_length] + (
        "..." if len(paper_text) > max_length else ""
    )

    prompt = f"""Please analyze the following academic paper and provide a summary in the specified format:

Paper text: {truncated_text}

Please provide:
1. A concise abstract summary in 3-5 sentences
2. Key findings and conclusions
3. Experimental results/methodology (if applicable)

Format your response exactly as follows:

**Abstract Summary**
[Your 3-5 sentence summary here]

**Key Findings**
• [Main finding/conclusion 1]
• [Main finding/conclusion 2]
• [Main finding/conclusion 3]

**Methodology & Results**
[Summary of methods and key results if applicable]

---"""

    try:
        st.info(f"처리할 텍스트 길이: {len(paper_text)}")
        if not paper_text or len(paper_text.strip()) < 100:
            st.error("텍스트가 너무 짧거나 비어 있습니다.")
            return None

        with st.spinner("논문을 요약하는 중..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research paper analyst specializing in creating clear, structured summaries of academic papers. Focus on extracting key information and presenting it in a well-organized format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            summary = response.choices[0].message["content"]
            return summary.strip()

    except Exception as e:
        st.error(f"요약 중 오류가 발생했습니다: {str(e)}")
        return None


def main():
    st.title("📚 논문 검색 및 분석기")

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
        4. 논문 요약 보기를 클릭하면 AI가 생성한 요약문을 볼 수 있습니다
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

    if "search_results" in st.session_state:
        st.header("검색 결과")

        for idx, result in enumerate(st.session_state.search_results):
            pdf_key = f"pdf_content_{idx}"  # pdf_text -> pdf_content
            summary_key = f"summary_content_{idx}"  # summary -> summary_content

            with st.expander(f"{result.title}"):
                # 논문 기본 정보
                st.markdown(f"### {result.title}")
                st.markdown(
                    f"**저자:** {', '.join([str(author) for author in result.authors])}"
                )
                st.markdown(f"**카테고리:** {result.primary_category}")
                st.markdown(f"**출판일:** {result.published.strftime('%Y-%m-%d')}")
                if result.doi:
                    st.markdown(f"**DOI:** {result.doi}")

                st.markdown("### 초록")
                st.markdown(result.summary.replace("\n", " "))
                st.markdown(f"[PDF 링크]({result.pdf_url})")

                # PDF 텍스트 및 요약 버튼
                # PDF 텍스트 추출 버튼
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("PDF 텍스트 보기", key=f"pdf_{idx}"):
                        with st.spinner("PDF 텍스트를 추출하는 중..."):
                            pdf_text = extract_pdf_text(result.pdf_url)
                            if pdf_text:
                                st.session_state[pdf_key] = pdf_text
                                st.success("PDF 텍스트 추출이 완료되었습니다!")
                            else:
                                st.error("PDF 텍스트 추출에 실패했습니다.")

                # AI 요약 버튼
                with col2:
                    if pdf_key in st.session_state:
                        if st.button("논문 요약 보기", key=f"summary_{idx}"):
                            with st.spinner("AI가 논문을 요약하는 중..."):
                                text_to_summarize = st.session_state[pdf_key]
                                st.info(f"텍스트 길이: {len(text_to_summarize)} 문자")

                                summary = summarize_paper(text_to_summarize)
                                if summary:
                                    st.session_state[summary_key] = summary
                                    st.success("논문 요약이 완료되었습니다!")
                                else:
                                    st.error("논문 요약에 실패했습니다.")

                # 탭으로 전문과 요약문 구분
                if pdf_key in st.session_state or summary_key in st.session_state:
                    tab1, tab2 = st.tabs(["논문 전문", "AI 요약"])

                    with tab1:
                        if pdf_key in st.session_state:
                            st.text_area(
                                "논문 전문",
                                value=st.session_state[pdf_key],
                                height=300,
                                key=f"pdf_text_area_{idx}",
                            )
                            # str로 변환하여 다운로드
                            text_data = str(st.session_state[pdf_key])
                            st.download_button(
                                label="텍스트 파일로 다운로드",
                                data=text_data,
                                file_name=f"{result.title}.txt",
                                mime="text/plain",
                                key=f"download_{idx}",
                            )

                    with tab2:
                        if summary_key in st.session_state:
                            st.markdown(st.session_state[summary_key])
                            # str로 변환하여 다운로드
                            summary_data = str(st.session_state[summary_key])
                            st.download_button(
                                label="요약문 다운로드",
                                data=summary_data,
                                file_name=f"{result.title}_summary.txt",
                                mime="text/plain",
                                key=f"download_summary_{idx}",
                            )


if __name__ == "__main__":
    st.set_page_config(
        page_title="ArXiv Paper Viewer & Analyzer",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    main()
