#!/usr/bin/python3

import smtplib #importing the module
import sys, os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def main(file):
    receiver='torhaakon2012_UTJkj4@kindle.com'
    sender='torhoaakon@gmail.com'
    password = "igexqbjdzyfdgvyz" # os.environ.get("GMAIL_PASSWORD")


    message = constructMessage(sender, receiver, file)
    sendEmail(sender, password, receiver, message)


def constructMessage(sender_add, receiver_add, file):
    message = MIMEMultipart()
    
    message["From"] = sender_add
    message['To'] = receiver_add
    message['Subject'] = "Email from python"
    
    attach = open(file, "rb")
    
    obj = MIMEBase('application','octet-stream')
    
    obj.set_payload((attach).read())
    encoders.encode_base64(obj)
    obj.add_header('Content-Disposition',"attachment; filename= "+file)
    
    message.attach(obj)
    attach.close()
    return message.as_string()

def sendEmail(sender_add, password, receiver_add, message):
    #creating the SMTP server object by giving SMPT server address and port number
    smtp_server=smtplib.SMTP("smtp.gmail.com",587)
    smtp_server.ehlo()
    smtp_server.starttls() 
    smtp_server.ehlo() 
    
    smtp_server.login(sender_add,password)
    
    smtp_server.sendmail(sender_add, receiver_add, message)
    print('Successfully the mail is sent') 
    
    smtp_server.quit() #terminating the server

def usage(prg):
    print(f"Usage: {prg} <file>")
    print("")
    print("Send a file to my kinlde using email!")

if __name__ == '__main__':
    if (sys.argv[1] == '--help'):
        usage(sys.argv[0])
        sys.exit(0)

    if len(sys.argv) < 2: 
        print("ERR: No enough arguments!")
        usage()
        sys.exit(1)
    
    main(sys.argv[1])
