import smtplib, imaplib, email, os, datetime
from typing import final
from dotenv import load_dotenv

load_dotenv()

sent_from = os.environ['EMAIL']
password = os.environ['PW']
forward_to = ""

def send_email(message):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(sent_from, password)
        to = [forward_to]
        server.sendmail(sent_from, to, message)
    except:
        pass
    server.close()

def logger(msg_num, msg = None):
    print(f"{num}", end="\r")
    with open("state.txt", "w") as state:
        state.write(msg_num)
    if msg:
        with open("log.txt", "a") as log:
            log.write(f"{msg_num} | {datetime.datetime.now().isoformat()} | {msg}\n")

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
                message = email.message_from_string(email_data.decode('utf-8'))
                original_from = message.get("From")
                original_subject = message.get("Subject")
                message.replace_header("To", forward_to)
                message.replace_header("From", sent_from)
                good_headers = [
                    "Date",
                    "Subject",
                    "From",
                    "To",
                    "Content-Type",
                    "MIME-Version",
                ]
                for k, v in message.items():
                    if k not in good_headers: message.replace_header(k, None)
                # send_email(message.as_string())
                logger(num, msg=f"Success: {original_from} : {original_subject}")
            except Exception as e:
                logger(num, msg=e)
                
    con.close()