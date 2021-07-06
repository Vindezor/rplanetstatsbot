import os
import aiohttp
import asyncio
import requests

URL_API = os.getenv('URL_API')

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