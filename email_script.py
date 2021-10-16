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
    # get the data from the message
    original = email.message_from_string(email_data.decode('utf-8'))

    # remove any attachments
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
    
    # remove any problematic headers
    for k, _v in original.items():
        if k not in good_headers: original.replace_header(k, None)

    # keep track of the original sender and subject
    original_from = original.get("From")
    original_subject = original.get("Subject")

    # create the message that we will forward
    new = MIMEMultipart("mixed")
    body = MIMEMultipart("alternative")
    body.attach( MIMEText("(auto-forwarded)", "plain") )
    body.attach( MIMEText("<html>(auto-forwarded)</html>", "html") )
    new.attach(body)

    # set headers appropriately
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
    con.login(sent_from, password) 
    print("Using the inbox...")
    resp, total = con.select('Inbox') 
    print(f"Total messages: {total[0].decode('utf-8')}")

    # if we ran this script previously, start where we left off
    try:
        with open("state.txt", "r") as state:
            last_msg = int(state.readline())
    except FileNotFoundError:
        last_msg = -1

    typ, data = con.search(None, 'ALL')
    # loop over the indices in the inbox...
    for num in data[0].decode('utf-8').split():

        # ...until we find the one after where we left off
        if int(num) > last_msg:
            try:
                # fetch the email at that index
                typ, data = con.fetch(num, '(RFC822)')
                
                # get the meat of the email
                email_data = data[0][1]
                
                # form the forwarded message
                new, original_from, original_subject = create_msg(email_data)
                
                # send the email to the farwarding address
                send_email(new.as_string())
                
                # set this message as read
                con.store(num, '+FLAGS', '\Seen')

                logger(num, msg=f"Success: {original_from} : {original_subject}")
            except Exception as e:
                logger(num, msg=f"ERROR: {original_from} : {original_subject} {e}")
                
    con.close()