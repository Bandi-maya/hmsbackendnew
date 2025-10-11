from flask_mail import Message

from extentions import mail


def send_email(subject, recipients, body, sender='your_email@gmail.com'):
    msg = Message(subject=subject,
                  sender=sender,
                  recipients=recipients,
                  body=body)
    mail.send(msg)