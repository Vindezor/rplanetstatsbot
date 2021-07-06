import telebot, requests, os
from flask import Flask, request
from resources.codes import codes
import aiohttp
import asyncio

KEY = os.getenv('KEY')
URL_API = os.getenv('URL_API')
URL_BOT = os.getenv('URL_BOT')
DEC = int(os.getenv('DEC'))

bot = telebot.TeleBot(KEY)
server = Flask(__name__)

def getTableRows(session, code, table, scope, lower, upper):
    send = {
        "json": True,
        "code": code,
        "table": table,
        "scope": scope,
        "lower_bound": lower,
        "upper_bound": upper,
        "limit": 100
    }
    return session.post(URL_API + "/get_table_rows",json=send)

async def miningPower(account):
    async with aiohttp.ClientSession() as session:
        #VEMOS TODAS LAS POOLS
        send = {
        "json": True,
        "code": "s.rplanet",
        "table": "pools",
        "scope": "s.rplanet",
        "lower_bound": "",
        "upper_bound": "",
        "limit": 1000
        }   
        poolinfo = requests.post(URL_API + "/get_table_rows", json=send).json()
        mining = {}
        tasks = []
        #VEMOS TODAS LAS ROW EN POOLINFO
        for row in poolinfo['rows']:
            tasks.append(getTableRows(session, "s.rplanet", "accounts", row['id'], account, account))
        responses = await asyncio.gather(*tasks)
        for response in responses:
            resp = await response.json()
            if resp['rows']:
                mining[poolinfo['rows'][responses.index(response)]['id']] = resp
        #VEMOS TODA LA DATA EN POOL INFO PARA VER SI ESTA EN EL MINING
        for data in poolinfo['rows']:
            if data['id'] in mining:
                fraction = float(data['fraction'].split(' ')[0])
                mining[data['id']]['fraction'] = fraction
                mining[data['id']]['pool'] = int(data['staked'])
        #CALCULAMOS EL PODER DE MINADO DE CADA UNO
        for data in mining:
            if data == 's.rplanet':
                staked = mining[data]['rows'][0]['staked']
                mining[data]['power'] = staked / 10000
            else:
                staked = mining[data]['rows'][0]['staked']
                poolreward = mining[data]['fraction']
                poolstaked = mining[data]['pool']
                mining[data]['power'] = staked * poolreward / poolstaked
        
        return mining

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
            #VERIFICAMOS SI LA CUENTA EXISTE
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
                    #CALCULAMOS LOS STATS
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

@server.route('/' + KEY, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=URL_BOT + KEY)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))