from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from requests import get
from urllib.request import urlopen
import re
#from collections import defaultdict
import time
import random
from datetime import datetime
#import yagmail
import gunicorn
import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content


headers = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})

title_list = []
length = len(BeautifulSoup(
            get('https://coinranking.com/exchange/2Vu9j1PmUbx+kraken/coins', 
            headers=headers).text, 
            'html.parser').find_all('td',class_="table__cell table__cell--3-of-8 table__cell--s-6-of-10"))
for crypto in range(length):
    crypto_name = str(BeautifulSoup(
            get('https://coinranking.com/exchange/2Vu9j1PmUbx+kraken/coins', 
                headers=headers).text, 
                'html.parser').find_all('td',class_="table__cell table__cell--3-of-8 table__cell--s-6-of-10")[crypto].find_all(
                href=True)[0]).split("\n")[1].replace(" ", "")
    title_list.append(crypto_name)



price_data = pd.DataFrame()
counter_1 = 0 #counter for 60 minute allerts
counter_12 = 0


# SENDER_EMAIL = os.environ("GMAIL_SMTP_USER")
# SENDER_APP_PASSWORD = os.environ("GMAIL_SMTP_PASSWORD")
# RECEIVER_EMAIL = "hornpeti@gmail.com"

# test_sub = "Test mail"
# tect_cont = "Test content"

# with yagmail.SMTP(SENDER_EMAIL, SENDER_APP_PASSWORD) as yag:
#             yag.send(RECEIVER_EMAIL, test_sub, tect_cont)

sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
from_email = Email(os.environ.get('SENDER_EMAIL'))
to_email = To(os.environ.get('RECEIVER_EMAIL'))
subject = "Crypto tracker try"
content = Content("text/plain", "Trying sendgrid")
mail = Mail(from_email, to_email, subject, content)

# Get a JSON-ready representation of the Mail object
mail_json = mail.get()

# Send an HTTP POST request to /mail/send
response = sg.client.mail.send.post(request_body=mail_json)

while True:
    if datetime.now().time().hour != 0:
        av_cryptos = []
        price_list = []
        counter_1 += 1
        counter_12 += 1

        for item in range(len(title_list)):

            try:

                try:

                    price = float(
                        BeautifulSoup(
                            get('https://coinmarketcap.com/currencies/{}/'.format(title_list[item])).text,
                            'html.parser').find_all(
                            "div",
                            class_='priceValue')[0].text.replace(
                            '$', '').replace(",", ""))

                except ConnectionError:

                    price = np.nan
                    time.sleep(250)
                    continue

                av_cryptos.append(title_list[item])
                price_list.append(price)
                # print(price)

                time.sleep(6)

            except IndexError:
                # print(title_list[item])
                continue

        now = datetime.now().time()
        price_data['Crypto names'] = av_cryptos
        price_data[str(now.hour) + ':' + str(now.minute)] = price_list

        # 20 minute allert
        if len(price_data.columns) >= 3:

            price_diff = dict(zip(price_data['Crypto names'].to_list(),
                                  list(price_data[price_data.columns.to_list()[-1]] /
                                       price_data[price_data.columns.to_list()[-2]])))

            big_price_inc = {}

            for name, value in price_diff.items():
                if value > 1.05:
                    big_price_inc[name] = value

            if len(big_price_inc) > 0:
                subject = '20 minutes alert {}'.format(str(datetime.now()))
                content = Content("text/plain", "List of cryptos with more than 5%-point price increase in the last 20 minutes: " +
                                 str(big_price_inc))
                mail = Mail(from_email, to_email, subject, content)
                mail_json = mail.get()
                response = sg.client.mail.send.post(request_body=mail_json)
            
        else:
            pass

        # 60 minute allert
        if counter_1 == 4:

            price_diff_60 = dict(zip(price_data['Crypto names'].to_list(),
                                     list(price_data[price_data.columns.to_list()[-1]] /
                                          price_data[price_data.columns.to_list()[-4]])))

            big_price_inc_60 = {}

            for name, value in price_diff_60.items():
                # have to set correct rate
                if value > 1.15:
                    big_price_inc_60[name] = value

            counter_1 = 0

            if len(big_price_inc_60) > 0:
                subject = '60 minutes alert {}'.format(str(datetime.now()))
                content = Content("text/plain", "List of cryptos with more than 15%-point price increase in the last 60 minutes: " + 
                                  str(big_price_inc_60))
                mail = Mail(from_email, to_email, subject, content)
                mail_json = mail.get()
                response = sg.client.mail.send.post(request_body=mail_json)

        else:
            pass

        # 12 hour allert
        if counter_12 == 37:

            price_diff_12hour = dict(zip(price_data['Crypto names'].to_list(),
                                         list(price_data[price_data.columns.to_list()[-1]] /
                                              price_data[price_data.columns.to_list()[-33]])))

            big_price_inc_12hour = {}

            for name, value in price_diff_12hour.items():
                # have to set correct rate
                if value > 1.2:
                    big_price_inc_12hour[name] = value

            counter_12 = 0

            if len(big_price_inc_12hour) > 0:
                subject = '12 hour alert {}'.format(str(datetime.now()))
                content = Content("text/plain", "List of cryptos with more than 20%-point price increase in the last 12 hours: " + 
                                  str(big_price_inc_12hour))
                mail = Mail(from_email, to_email, subject, content)
                mail_json = mail.get()
                response = sg.client.mail.send.post(request_body=mail_json)

        else:
            pass

        # 20 minutes sleep (16 min + 4 min runtime) - 960 will be 20 min
        time.sleep(960)


    else:

        price_diff_daily = dict(zip(price_data['Crypto names'].to_list(),
                                    list(price_data[price_data.columns.to_list()[-1]] /
                                         price_data[price_data.columns.to_list()[1]])))

        subject = 'Daily recap {}'.format(str(datetime.now()))
        content = Content("text/plain", "Daily crypto price changes: " + str(price_diff_daily))
        mail = Mail(from_email, to_email, subject, content)
        mail_json = mail.get()
        response = sg.client.mail.send.post(request_body=mail_json)

        #print("reset time")
        time.sleep(3600)
        # save data (maybe to big dataframe? - maybe less important)
        price_data = pd.DataFrame()

        title_list = []
        length = len(BeautifulSoup(
            get('https://coinranking.com/exchange/2Vu9j1PmUbx+kraken/coins',
                headers=headers).text,
            'html.parser').find_all('td', class_="table__cell table__cell--3-of-8 table__cell--s-6-of-10"))
        for crypto in range(length):
            crypto_name = str(BeautifulSoup(
                get('https://coinranking.com/exchange/2Vu9j1PmUbx+kraken/coins',
                    headers=headers).text,
                'html.parser').find_all(
                'td', class_="table__cell table__cell--3-of-8 table__cell--s-6-of-10")[crypto].find_all(
                href=True)[0]).split("\n")[1].replace(" ", "")

            title_list.append(crypto_name)




server = app.server
if __name__ == "__main__":
    app.run_server(debug=False)
