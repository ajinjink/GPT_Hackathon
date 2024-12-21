import os

import openai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")


def summarize_paper(paper_text):
    prompt = f"""
        다음 논문 {paper_text} 다음 정보를 추출해 주세요:
        1. **요약문(Abstract)**: 논문의 주제를 간결하고 명확하게 요약한 5문장 이내로 영어로 작성해주세요. (아래 [] 속 내용은 출력하지 마세요.)
            문장 1) [영어 요약문]
        2. **Key Phrases**: 논문의 내용을 핵심 주제와 기술을 영어로 작성해주세요.(아래 [] 내용은 출력하지 말고, 각 항목별 3문장 이내로 작성해주세요.)
            문장 1) [논문 전체 내용 요약]
            문장 2) [Conclusion 요약]
            문장 3) [실험 내용 요약] (논문의 내용에 실험이 있다면 문장 3을 출력하고, 없다면 출력하지 마세요.)


        반드시 다음 형식에 맞춰 결과를 출력해주세요:

        ---
        
        **요약문(Abstract)**:  
        [문장 1]

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
                    "content": "당신은 논문을 읽고 주제를 파악해서 논문에서 핵심 내용, 기술 등을 요약해서 알려주는 논문 인용 컨설턴트입니다.",
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
