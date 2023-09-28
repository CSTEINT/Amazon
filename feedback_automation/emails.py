from simplegmail import Gmail
from datetime import datetime
# import logging
from simplegmail.query import construct_query
gmail = Gmail()
import os

path = os.getcwd()
# logger = logging.get_logger('__name__')


def get_sheet_and_timings():
    query_params = {
        "newer_than": (36, "hour"),
        # "unread": True,
        # "labels":[["Work"], ["Homework", "CS"]]
    }

    messages = gmail.get_messages(query=construct_query(query_params))
    message = [message for message in messages if 'varvic13@gmail.com' in message.sender]
    if message:
        message=message[0]
    if message.attachments:
        for attm in message.attachments:
            attm.save(overwrite=True)
            print(attm.filename)
            return attm.filename
              # downloads and saves each attachment under it's stored
                         # filename. You can download without saving with `attm.download()


def send_mail(filename):
    params = {
      "to": "varvic13@gmail.com",
      "sender": "venu@cste.international",
      # "cc": ["bob@bobsemail.com"],
      # "bcc": ["marie@gossip.com", "hidden@whereami.com"],
      "subject": "Day O/P Sheet",
      "msg_html": f"<h1>Hello Team!</h1><br />Output for the day {datetime.now().strftime('%Y-%m-%d')}",
      # "msg_plain": "Hi Team, \nThis Updated Sheet Details.",
      "attachments": [f"{path}\\amazon_listing.csv"],
      "signature": True  # use my account signature
    }
    message = gmail.send_message(**params)
    # logger


if __name__=="__main__":
    send_mail('amazon_listing.csv')