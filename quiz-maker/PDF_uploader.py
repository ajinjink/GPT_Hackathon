import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import json
from openai import OpenAI


class PDFQuestionGenerator:
    def __init__(self, api_key):
        """
        PDF에서 텍스트를 추출하고 질문을 생성하는 클래스.
        - api_key: OpenAI API 키
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def extract_text_from_range(self, pdf_file_path, start_page, end_page):
        """
        PDF에서 지정된 범위의 텍스트를 추출합니다.
        - pdf_file_path: PDF 파일 경로
        - start_page: 시작 페이지 (1부터 시작)
        - end_page: 끝 페이지 (1부터 시작)
        """
        reader = PdfReader(pdf_file_path)
        pages = reader.pages
        text = ""
        for page_number in range(start_page - 1, end_page):
            sub = pages[page_number].extract_text()
            text += sub
        return text

    def split_text_to_chunks(self, text, details):
        """
        텍스트를 청크 단위로 쪼갭니다.
        - text: 입력 텍스트 (str)
        - details: 문제 상세도 (1, 2, 3 중 선택)
        """
        chunk_size = 250 * (4 - details)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        splits = text_splitter.split_text(text)
        print("생성된 chunk 수:", len(splits))
        return splits

    def create_questions_from_chunk(self, chunk, number_of_questions, feedback=''):
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
                            "problems": {
                                "type": "array",
                                "description": "A collection of problems, where each problem is paired with its answer.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "problem": {
                                            "type": "string",
                                            "description": "The statement of the problem."
                                        },
                                        "answer": {
                                            "type": "string",
                                            "description": "The solution or answer to the problem."
                                        }
                                    },
                                    "required": ["problem", "answer"],
                                    "additionalProperties": False
                                }
                            },
                            "number_of_problems": {
                                "type": "number",
                                "description": "The total number of problems represented in the problems array."
                            }
                        },
                        "required": ["problems", "number_of_problems"],
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

    def create_questions_with_feedback(self, splits, number_of_questions):
        """
        청크 단위로 문제를 생성하고 피드백을 반영합니다.
        - splits: 텍스트 청크 리스트
        - number_of_questions: 총 생성할 문제 수
        """
        all_questions = []

        for i, chunk in enumerate(splits):
            questions = self.create_questions_from_chunk(chunk, number_of_questions // len(splits))
            print(f"\n청크 {i+1}의 문제:")
            parsed_q = json.loads(questions)
            print(parsed_q)

            is_feedback = int(input("피드백 여부를 입력하세요 (하고 싶으면 1, 하고 싶지 않으면 0): "))

            while is_feedback == 1:
                feedback = input("피드백 내용을 입력해주세요.")
                questions = self.create_questions_from_chunk(chunk, number_of_questions // len(splits), feedback=feedback)
                print(f"\n청크 {i+1}의 문제:")
                parsed_q = json.loads(questions)
                print(parsed_q)
                is_feedback = int(input("피드백 여부를 입력하세요 (하고 싶으면 1, 하고 싶지 않으면 0): "))

            all_questions.append(questions)

        return all_questions

    def save_questions_to_json(self, all_questions, output_file="questions.json"):
        """
        생성된 문제를 JSON 파일로 저장합니다.
        - all_questions: 문제 리스트
        - output_file: 저장할 JSON 파일 경로
        """
        final_questions = []
        for i, q in enumerate(all_questions):
            print(f"\n청크 {i+1}의 문제:")
            parsed_q = json.loads(q)
            print(parsed_q)

            for x in parsed_q["problems"]:
                final_questions.append({
                    "question": x["problem"],
                    "answer": x["answer"]
                })

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(final_questions, file, indent=2, ensure_ascii=False)

# 사용 예시
if __name__ == "__main__":
    # 환경 변수 로드
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    # 클래스 초기화
    pdf_generator = PDFQuestionGenerator(api_key=api_key)

    # PDF 파일 경로 및 설정
    PDF_FILE_PATH = "/Users/sehyun/forif/IVS_08_MPORT.pdf"
    start_page = 5
    end_page = 10
    number_of_questions = 10

    # 텍스트 추출 및 문제 생성
    extracted_text = pdf_generator.extract_text_from_range(PDF_FILE_PATH, start_page, end_page)
    splits = pdf_generator.split_text_to_chunks(extracted_text, details=1)
    all_questions = pdf_generator.create_questions_with_feedback(splits, number_of_questions=number_of_questions)

    # JSON 저장
    pdf_generator.save_questions_to_json(all_questions)