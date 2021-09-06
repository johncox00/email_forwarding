import smtplib, imaplib, email, os, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage

from typing import final
from dotenv import load_dotenv

load_dotenv()

sent_from = os.environ['EMAIL']
password = os.environ['PW']
forward_to = os.environ['FWD']
good_headers = [
                    "Date",
                    "Subject",
                    "From",
                    "To",
                    "Content-Type",
                    "MIME-Version",
                    "Message-ID"
                ]

def send_email(message):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.ehlo()
        server.login(sent_from, password)
        to = [forward_to]
        server.sendmail(sent_from, to, message)

def logger(msg_num, msg = None):
    print(f"{num}", end="\r")
    with open("state.txt", "w") as state:
        state.write(msg_num)
    if msg:
        with open("log.txt", "a") as log:
            log.write(f"{msg_num} | {datetime.datetime.now().isoformat()} | {msg}\n")

def create_msg(email_data):
    original = email.message_from_string(email_data.decode('utf-8'))
    for part in original.walk():
        if (part.get('Content-Disposition')
            and part.get('Content-Disposition').startswith("attachment")):

            part.set_type("text/plain")
            part.set_payload("Attachment removed: %s (%s, %d bytes)"
                            %(part.get_filename(), 
                            part.get_content_type(), 
                            len(part.get_payload(decode=True))))
            del part["Content-Disposition"]
            del part["Content-Transfer-Encoding"]
    for k, _v in original.items():
        if k not in good_headers: original.replace_header(k, None)
    original_from = original.get("From")
    original_subject = original.get("Subject")

    new = MIMEMultipart("mixed")
    body = MIMEMultipart("alternative")
    body.attach( MIMEText("(auto-forwarded)", "plain") )
    body.attach( MIMEText("<html>(auto-forwarded)</html>", "html") )
    new.attach(body)

    new["Message-ID"] = email.utils.make_msgid()
    new["In-Reply-To"] = original["Message-ID"]
    new["References"] = original["Message-ID"]
    new["Subject"] = "FWD: "+original["Subject"]
    new["To"] = forward_to
    new["From"] = sent_from
    new.attach( MIMEMessage(original) )
    return new, original_from, original_subject

with imaplib.IMAP4_SSL(host="imap.gmail.com") as con:
    print("Logging in...")
    # logging the user in
    con.login(sent_from, password) 
    print("Using the inbox...")
    # calling function to check for email under this label
    resp, total = con.select('Inbox') 
    print(f"Total messages: {total[0].decode('utf-8')}")

    try:
        with open("state.txt", "r") as state:
            last_msg = int(state.readline())
    except FileNotFoundError:
        last_msg = -1

    typ, data = con.search(None, 'ALL')
    for num in data[0].decode('utf-8').split():
        if int(num) > last_msg:
            try:
                typ, data = con.fetch(num, '(RFC822)')
                email_data = data[0][1]
                
                new, original_from, original_subject = create_msg(email_data)
                
                send_email(new.as_string())
                
                logger(num, msg=f"Success: {original_from} : {original_subject}")
            except Exception as e:
                logger(num, msg=f"ERROR: {original_from} : {original_subject} {e}")
                
    con.close()