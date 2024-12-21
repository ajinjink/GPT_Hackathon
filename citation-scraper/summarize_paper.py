import os

import openai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")


def summarize_paper(paper_text):

    prompt = f"""
        다음 논문 {paper_text} 다음 정보를 추출해 주세요:
        1. **논문 정보**: 논문의 제목(저자,연도)를 정확히 기재해주세요.
        2. **요약문(Abstract)**: 논문의 주제를 간결하고 명확하게 요약한 3~5문장을 영어와 한국어로 각각 작성해주세요.(아래 [] 속 내용은 출력하지 마세요.)
            문장 1) [영어 요약문]
            문장 2) [한국어 요약문]  
        3. **Key Phrases**: 논문의 내용을 핵심 주제와 기술을 작성해주세요.(아래 [] 내용은 출력하지 않고, 각 항목 별 3문장 이내로 작성해주세요.)
            문장 1) [논문 전체 내용 요약]
            문장 2) [conclusion 요약]
            문장 3) [실험 내용 요약](논문의 내용에 실험이 있다면 문장3을 출력하고, 없다면 출력하지 마세요.)


        결과는 다음 형식으로 작성해주세요:

        ---

        **논문 제목**: [논문 제목]    

        **요약문(Abstract)**:  
        1. [문장 1]
        2. [문장 2]

        **Key Phrases**: 
        1. [문장 1]
        2. [문장 2]
        3. [문장 3]
        """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 논문을 읽고 주제를 파악해서 논문에서 핵심 내용,기술 등을 요약해서 알려주는 논문 인용 컨설턴트입니다.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    paper_text = """dummy text
    """
    result = summarize_paper(paper_text)

    if result:
        print(result)
    else:
        print("논문 정보를 추출하지 못했습니다.")
