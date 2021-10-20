import smtplib, imaplib, email, os, datetime, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage
from email.message import EmailMessage

from typing import final
from dotenv import load_dotenv

load_dotenv()

# need the email to come from the original sender
# emails are currently showing up as an attachment

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
context = ssl.create_default_context()

def send_email(message, original_from):
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        print("did the ehlo")
        server.login(sent_from, password)
        print("logged in")
        to = [forward_to]
        msg = message.encode('utf8')
        print("encoded the msg")
        server.sendmail(original_from, to, msg)
        print("sent the email")

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
    # original_body = None
    # # remove any attachments
    # for part in original.walk():
    #     ctype = part.get_content_type()
    #     cdispo = str(part.get('Content-Disposition'))
    #     if (cdispo
    #         and cdispo.startswith("attachment")):
    #         part.set_type("text/plain")
    #         part.set_payload("Attachment removed: %s (%s, %d bytes)"
    #                         %(part.get_filename(), 
    #                         part.get_content_type(), 
    #                         len(part.get_payload(decode=True))))
    #         del part["Content-Disposition"]
    #         del part["Content-Transfer-Encoding"]
        
    #     elif ctype == 'text/plain' and 'attachment' not in cdispo:
    #         original_body = part.get_payload(decode=True)  # decode
    
    # remove any problematic headers
    for k, _v in original.items():
        if k not in good_headers: original.replace_header(k, None)

    # keep track of the original sender and subject
    original_from = original.get("From")
    print(f"ORIG FROM: {original_from}")
    print(f"ORIG TYPE: {type(original)}")
    original_subject = original.get("Subject")
    fwd = f"""
    ---------Forwarded Message--------- 
    {original_from}
    """
    # original.set_content(f"{fwd}\n{original.get_content()}")
    original.preamble = fwd
    # # create the message that we will forward
    # new = MIMEMultipart("mixed")
    # body = MIMEMultipart("alternative")
    # # body.attach( MIMEText(original_body.decode("utf-8"), "plain") )
    # body.attach( MIMEText(f"<html>{original_body.decode('utf-8')}</html>", "html") )
    # new.attach(body)

    # # set headers appropriately
    # new["Message-ID"] = email.utils.make_msgid()
    # new["In-Reply-To"] = original["Message-ID"]
    # new["References"] = original["Message-ID"]
    # new["Subject"] = "FWD: "+original["Subject"]
    # new["To"] = forward_to
    # new["From"] = original_from
    # # new.attach( MIMEMessage(original) )
    # return new, original_from, original_subject
    return original, original_from, f"fwd: {original_subject}"

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
        print(f"Starting num {num}")
        # ...until we find the one after where we left off
        if int(num) > last_msg:
            print(f"in the loop! {num}")
            try:
                # fetch the email at that index
                typ, data = con.fetch(num, '(RFC822)')
                print("fetched")
                # get the meat of the email
                email_data = data[0][1]
                print("got the email")
                # form the forwarded message
                new, original_from, original_subject = create_msg(email_data)
                print("made the email")
                # send the email to the farwarding address
                send_email(new.as_string(), original_from)
                print("sent the email")
                # set this message as read
                con.store(num, '+FLAGS', '\Seen')
                print("updated read status")
                logger(num, msg=f"Success: {original_from} : {original_subject}")
            except Exception as e:
                logger(num, msg=f"ERROR: {original_from} : {original_subject} {e}")
            break 
    con.close()