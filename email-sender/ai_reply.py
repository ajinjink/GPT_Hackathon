import imaplib
import email
from email.header import decode_header, make_header
import smtplib
from email.mime.text import MIMEText
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate


# --- Email Reader Class ---
class EmailReader:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.imap = None

    def connect(self):
        self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
        self.imap.login(self.user, self.password)

    def fetch_latest_email(self):
        self.imap.select("INBOX")
        status, messages = self.imap.search(None, 'ALL')
        messages = messages[0].split()
        latest_email_id = messages[-1]
        res, msg = self.imap.fetch(latest_email_id, "(RFC822)")
        raw_email = msg[0][1]
        return email.message_from_bytes(raw_email)

    def disconnect(self):
        self.imap.close()
        self.imap.logout()

    def get_email_body(self, email_message):
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    return part.get_payload(decode=True).decode('utf-8')
        else:
            return email_message.get_payload(decode=True).decode('utf-8')


# --- Email Responder Class ---
class EmailResponder:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.memory = ConversationBufferMemory()
        self.template = """
        당신은 매우 공손하고 성실한 대학생으로 행동해야 합니다. 
        다음 메일을 교수님께 답장하는 형식으로 작성하세요.

        대화 히스토리:
        {history}

        교수님의 메일:
        {input}

        학생의 답장:
        """
        self.prompt = PromptTemplate(input_variables=["history", "input"], template=self.template)
        self.conversation = ConversationChain(llm=self.llm, memory=self.memory, prompt=self.prompt)

    def generate_response(self, body, history=""):
        return self.conversation.predict(input=body, history=history)


# --- Email Sender Class ---
class EmailSender:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def send_email(self, receiver, subject, body):
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(self.user, self.password)

        msg = MIMEText(body, 'plain')
        msg['Subject'] = 'Re: ' + subject
        msg['From'] = self.user
        msg['To'] = receiver

        smtp.sendmail(self.user, receiver, msg.as_string())
        smtp.quit()


class FeedbackManager:
    def __init__(self, responder, history, body):
        """
        FeedbackManager 초기화
        """
        self.responder = responder
        self.history = history
        self.body = body
        self.response = None  # 현재 응답 상태 저장

    def generate_initial_response(self):
        """
        초기 답변 생성
        """
        self.response = self.responder.generate_response(self.body, self.history)
        print("\nInitial Response:")
        print(self.response)  # 초기 응답 출력
        return self.response

    def collect_feedback(self):
        """
        사용자 피드백 수집 및 답변 업데이트
        """
        while True:
            user_feedback = input("\nIs this response satisfactory? (Yes/No): ").strip().lower()
            if user_feedback == 'yes':
                print("\nFinal Response:")
                print(self.response)  # 최종 응답 출력
                print("The response has been accepted.")
                break
            elif user_feedback == 'no':
                feedback = input("Please provide your feedback: ")
                # 피드백을 기반으로 새로운 응답 생성
                updated_body = f"""
                이전 답장이 만족스럽지 못했습니다. 다음은 피드백입니다: {feedback}
                이 피드백을 반영하여 답장을 다시 작성하세요.

                교수님의 메일:
                {self.body}

                학생의 답장:
                """
                # 이전 응답 저장
                previous_response = self.response
                # 새로운 응답 생성
                self.response = self.responder.generate_response(updated_body)

                print("\nPrevious Response:")
                print(previous_response)
                print("\nUpdated Response:")
                print(self.response)  # 수정된 응답 출력
            else:
                print("Please enter 'Yes' or 'No'.")


# --- Email Processor Class ---
class EmailProcessor:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.reader = EmailReader(user, password)
        self.responder = EmailResponder()
        self.sender = EmailSender(user, password)

    def process_email(self):
        # Step 1: Read the latest email
        self.reader.connect()
        email_message = self.reader.fetch_latest_email()
        self.reader.disconnect()

        # Step 2: Parse email details
        fr = make_header(decode_header(email_message.get('From')))
        fr_str = str(fr)
        receiver = fr_str.split('<')[-1].strip('>')

        subject = str(make_header(decode_header(email_message.get('Subject'))))
        body = self.reader.get_email_body(email_message)

        # Display email content
        print("From (receiver):", receiver)
        print("Subject:", subject)
        print("Body:")
        print(body)

        # Step 3: Generate a response with feedback
        feedback_manager = FeedbackManager(self.responder, "", body)
        response = feedback_manager.generate_initial_response()
        print("\n작성된 답장:")
        print(response)

        feedback_manager.collect_feedback()
        final_response = feedback_manager.response

        # Step 4: Decide to send or not
        send_decision = input("답장을 보낼까요? (y/n): ").strip().lower()
        if send_decision == 'y':
            self.sender.send_email(receiver, subject, final_response)
            print("답장을 보냈습니다.")
        elif send_decision == 'n':
            print("답장을 보내지 않았습니다.")
        else:
            print("잘못된 입력입니다. 답장을 보내지 않았습니다.")


# --- Main Execution ---
if __name__ == "__main__":
    user = 'email'
    password = 'password'

    processor = EmailProcessor(user, password)
    processor.process_email()
