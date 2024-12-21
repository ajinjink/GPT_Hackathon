import os
import webbrowser
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
        response = requests.get(pdf_url)
        response.raise_for_status()

        pdf_file = BytesIO(response.content)
        pdf_reader = PdfReader(pdf_file)

        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        cleaned_text = text.replace("\n", " ").strip()
        return cleaned_text

    except Exception as e:
        st.error(f"PDF 처리 중 오류가 발생했습니다: {str(e)}")
        return None


def summarize_paper(paper_text):
    """논문 텍스트 요약"""
    max_length = 14000
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

### **Summary**
- [Your 3-5 sentence summary here]

### **Key Findings**
- [Main finding/conclusion 1]

- [Main finding/conclusion 2]

- [Main finding/conclusion 3]

### **Methodology & Results**
- [Summary of methods and key results if applicable]

"""

    try:
        if not paper_text or len(paper_text.strip()) < 100:
            st.error("텍스트가 너무 짧거나 비어 있습니다.")
            return None

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
        3. AI 요약 보기를 클릭하면 AI가 생성한 요약문을 볼 수 있습니다
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
            summary_key = f"summary_content_{idx}"

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

                # pdf 링크 버튼
                if st.button("PDF 링크", key=f"pdf_link_{idx}"):
                    webbrowser.open_new_tab(result.pdf_url)

                st.markdown("### 초록")
                st.markdown(result.summary.replace("\n", " "))
                # st.markdown(f"[PDF 링크]({result.pdf_url})")

                # AI 요약 버튼
                if st.button("AI 요약 보기", key=f"summary_{idx}"):
                    with st.spinner("PDF를 다운로드하고 요약하는 중..."):
                        # PDF 텍스트 추출
                        pdf_text = extract_pdf_text(result.pdf_url)

                        if pdf_text:
                            # 텍스트 요약
                            summary = summarize_paper(pdf_text)
                            if summary:
                                st.session_state[summary_key] = summary
                                st.success("논문 요약이 완료되었습니다!")
                            else:
                                st.error("논문 요약에 실패했습니다.")
                        else:
                            st.error("PDF 텍스트 추출에 실패했습니다.")

                # 요약문
                if summary_key in st.session_state:
                    st.markdown(st.session_state[summary_key])
                    # 요약문 다운로드 버튼
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
