from resources.codes import codes
from resources.functions import miningPower

import telebot
import os
import requests
import asyncio

KEY = os.getenv('KEY')
URL_API = os.getenv('URL_API')
DEC = int(os.getenv('DEC'))

bot = telebot.TeleBot(KEY)

@bot.message_handler(commands= ["start"])
def start(message):
    first_name = message.from_user.first_name
    bot.reply_to(message, f"*Welcome {first_name}!*👋\
\n\nI am 🤖*R-PlanetStatsBot* and I can show you your R-Planet Staking Stats.\
\n\nTo understand how I work, please press /help\
\n\n*WAX address for donations:* [ddgra.wam](https://wax.bloks.io/wallet/transfer) ❤️", parse_mode='MARKDOWN')

@bot.message_handler(commands= ["help"])
def help(message):
    bot.reply_to(message, 'Hi👋, how are you? to make your queries please use the following commands✅:\
\n\n/aether - To check your R-Planet staking stats\
\n\n<b>WAX address for donations:</b> <a href="https://wax.bloks.io/wallet/transfer"><b>ddgra.wam</b></a> ❤️', parse_mode='HTML')

#Mining stats
@bot.message_handler(commands=['aether'])
def aether(message):
    try:
        if message.text[7] == '@':
            account = ''
        else:
            account = message.text[8:]
            totalPower = 0
        if account:
            #Verifying if account exists
            send = {"account_name": account}
            response = requests.post(URL_API + '/get_account', json=send)
            if response.status_code == 200:
                mining = asyncio.run(miningPower(account))
                if mining:
                    resp = f'*🙍‍♂️Account: {account}*\n'
                    forCollect = []
                    for data in mining:
                        power = mining[data]['power']
                        if data in codes:
                            resp += f'\n*✅{codes[data]}:* {round(power,DEC)} A/h'
                        else:
                            resp += f'\n*✅{data}:* {round(power,DEC)} A/h'
                        totalPower += power
                        forCollect.append(float(mining[data]['rows'][0]['collected'].split(' ')[0]))
                    resp += f'\n\n*⚡️Total staking power: {round(totalPower, DEC)} A/h\n🌡Aether for claiming: {round(sum(forCollect), DEC)}*'
                    #Calculating stats
                    multiplier = [1,24,24*7,24*30,24*365]
                    time = ['Hourly','Daily','Weekly','Monthly','Yearly']
                    stats = ['AETHER', 'WAX', 'USD']
                    response_alcor = requests.get('https://wax.alcor.exchange/api/markets')
                    data = response_alcor.json()
                    response_coingecko = requests.get('https://api.coingecko.com/api/v3/coins/wax')
                    for par in data:
                        if par['base_token']['symbol']['name'] == 'WAX' and par['quote_token']['symbol']['name'] == 'AETHER':
                            aetherwax = par['last_price']
                            break
                    waxusd = response_coingecko.json()['market_data']['current_price']['usd']
                    price = [0,0,0,0,0]
                    for coin in stats:
                        if coin == 'AETHER':
                            resp += f'\n\n🌡*{coin}*'
                        elif coin == 'WAX':
                            resp += f'\n\n🟡*{coin}*'
                        else:
                            resp += f'\n\n💸*{coin}*'
                        for i in range(5):
                            if coin == 'AETHER':
                                price[i] = totalPower*multiplier[i]
                                resp += f'\n- {time[i]}: {round(price[i],DEC)}'
                            elif coin == 'WAX':
                                price[i] = price[i]*aetherwax
                                resp += f'\n- {time[i]}: {round(price[i],DEC)}'
                            else:
                                price[i] = price[i]*waxusd
                                resp += f'\n- {time[i]}: {round(price[i],DEC)}'

                    bot.reply_to(message, resp, parse_mode='MARKDOWN')
                else:
                    bot.reply_to(message,f'*‼️Account "{account}" does not have any asset on staking.*', parse_mode='MARKDOWN')
            else:
                bot.reply_to(message,f'*‼️Account "{account}" does not exist.*', parse_mode='MARKDOWN')
        else:
            bot.reply_to(message,'*‼️Command format:*\n\n/aether account.wam\n\nIf you need help press /help.', parse_mode='MARKDOWN')
    except:
        bot.reply_to(message,'*‼️Command format:*\n\n/aether account.wam\n\nIf you need help press /help.', parse_mode='MARKDOWN')