import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header, make_header
import itertools


class email_manage():
    def box_id(self, imap_list):
        for box in imap_list:
            if 'All' in str(box):
                return str(box).split('"')[-2]

    def fetch_email(self, user, password):

        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(user, password)

        imap.select(self.box_id(imap.list()[-1]))
        status, messages = imap.uid('search', None, 'ALL')
        messages = messages[0].split()

        memorys = []
        mails = []
        for recent in reversed(messages[-10:]):

            res, msg = imap.uid('fetch', recent, "(RFC822)")
            raw = msg[0][1].decode('utf-8')

            # raw에서 원하는 부분만 파싱하기 위해 email 모듈을 이용해 변환
            email_message = email.message_from_string(raw)            
            
            # 보낸 사람, 받는 사람
            try:
                message_type = 'sent'
                sender = user
                receiver = str(make_header(decode_header(email_message.get('Bcc'))))
            except:
                message_type = 'received'
                receiver = user
                sender = str(make_header(decode_header(email_message.get('From')))).split('<')[-1][:-1]

            # 메일 제목
            subject = str(make_header(decode_header(email_message.get('Subject'))))

            # 메일 내용
            body = ''
            if email_message.is_multipart():
                for part in email_message.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        body = part.get_payload(decode=True)  # decode
                        break
            else:
                body = email_message.get_payload(decode=True)
            
            try:
                body = body.decode('utf-8')
            except:
                pass
            # 시간
            try:
                time = str(make_header(decode_header(email_message.get('Received')))).split('\n')[-1].strip()

            except:
                time = str(make_header(decode_header(email_message.get('Date'))))
                    
            memory = {}
            memory['from'] = sender
            memory['to'] = receiver
            memory['content'] = body
            memory['timestamp'] = time
            memory['type'] = message_type
            memorys.append(memory)
            memory['title'] = subject.strip('Re: ')
            mails.append(memory)

        mails_combined = {}
        for i, v in itertools.groupby(mails, lambda i:i['title']):
            mails_combined[i] = list(v)

        return memorys, mails_combined

    def send_email(self, user, password, receiver, title, content):

        sender = user
        #587포트 및 465포트 존재
        smtp = smtplib.SMTP('smtp.gmail.com', 587)

        smtp.ehlo()

        smtp.starttls()

        #로그인을 통해 지메일 접속
        smtp.login(user, password)

        #내용을 입력하는 MIMEText => 다른 라이브러리 사용 가능
        msg = MIMEText(content)
        msg['Subject'] = title
        msg['From'] = sender
        msg['To'] = receiver

        #이메일을 보내기 위한 설정(Cc도 가능)
        smtp.sendmail(sender, receiver, msg.as_string())

        #객체 닫기
        smtp.quit()