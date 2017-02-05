import itchat
from itchat.content import TEXT
import threading
import os
import json
import configparser
from urllib import request, parse


configFile = 'default.config'
if os.path.exists('user.config'):
    configFile = 'user.config'
config = configparser.ConfigParser()
config.read(configFile)
robotUrl = config['tuling']['url']
robotKey = config['tuling']['key']
waitingTime = int(config['system']['waiting'])
outTime = int(config['system']['out'])
aftTime = int(config['system']['aft'])

debugState = config['system']['debug'] != 0
def debug(*data):
    if debugState:
        print(*data)

auto_reply_switch = True
auto_reply_pool = {}
waiting_pool = {}
chatting_pool = {}

def pop_waiting_list(username):
    print(username)
    if username in waiting_pool:
        waiting_pool.pop(username)
        debug('delete from waiting list')

def pop_chatting_list(username):
    print(username)
    if username in chatting_pool:
        chatting_pool.pop(username)
        debug('delete from chatting list')

def auto_reply(**msg):
    if not auto_reply_switch:
        return
    itchat.send('抱歉，我暂时无法回复，稍后我会联系您。 [自动回复]', toUserName=msg['FromUserName'])
    itchat.send('你可以尝试让机器人和你聊天。 回复“是”开始，回复”再见”结束。 [自动回复]', toUserName=msg['FromUserName'])
    waiting_pool[msg['FromUserName']] = auto_reply_pool[msg['FromUserName']]
    auto_reply_pool.pop(msg['FromUserName'])
    timer = threading.Timer(outTime, pop_waiting_list, args=(msg['FromUserName'],))
    timer.start()

def auto_reply_smart(**msg):
    if not auto_reply_switch:
        return
    debug(msg)
    data = {
        'key': robotKey,
        'info': msg['Text'][1:].strip(),
        'userid': msg['FromUserName']
    }
    data = parse.urlencode(data).encode()
    req = request.Request(url=robotUrl, data=data)
    res = request.urlopen(req)
    res = res.read().decode()
    res = json.loads(res)
    debug(res)
    if res['code'] == 100000:
        itchat.send('{0} [机器人]'.format(res['text']), toUserName=msg['FromUserName'])
    else:
        itchat.send('本宝宝拒绝服务。 [机器人]', toUserName=msg['FromUserName'])

@itchat.msg_register([TEXT])
def text_reply(msg):
    debug(msg)
    if msg['FromUserName'] == itchat.loginInfo['User']['UserName']:
        if msg['ToUserName'] == 'filehelper':
            global auto_reply_switch
            if msg['Text'] == '开始自动回复':
                auto_reply_switch = True
                itchat.send('自动回复：开启', msg['ToUserName'])
            elif msg['Text'] == '结束自动回复':
                auto_reply_switch = False
                itchat.send('自动回复：关闭', msg['ToUserName'])
        if msg['ToUserName'] in chatting_pool:
            timer = chatting_pool[msg['ToUserName']]
            timer.cancel()
        timer = threading.Timer(aftTime, pop_chatting_list, args=(msg['ToUserName'],))
        chatting_pool[msg['ToUserName']] = timer
        timer.start()
        if auto_reply_switch and msg['ToUserName'] in auto_reply_pool:
            debug('replied')
            timer = auto_reply_pool[msg['ToUserName']]['timer']
            timer.cancel()
            auto_reply_pool.pop(msg['ToUserName'])
    elif auto_reply_switch:
        if msg['FromUserName'] in chatting_pool:
            pass
        elif msg['FromUserName'] in auto_reply_pool:
            if auto_reply_pool[msg['FromUserName']]['reply_smart']:
                if msg['Text'] == '再见':
                    itchat.send('再见啦～ [机器人]', toUserName=msg['FromUserName'])
                    auto_reply_pool.pop(msg['FromUserName'])
                else:
                    auto_reply_smart(**msg)
        elif msg['FromUserName'] in waiting_pool:
            if msg['Text'] == '是':
                waiting_pool[msg['FromUserName']]['reply_smart'] = True
                auto_reply_pool[msg['FromUserName']] = waiting_pool[msg['FromUserName']]
                waiting_pool.pop(msg['FromUserName'])
                itchat.send('你可以和本宝宝说话啦。[机器人]', toUserName=msg['FromUserName'])
        else:
            timer = threading.Timer(waitingTime, auto_reply, kwargs=msg)
            auto_reply_pool[msg['FromUserName']] = {
                'timer': timer,
                'reply_smart': False
            }
            timer.start()

itchat.auto_login(True, enableCmdQR=2)
itchat.loginInfo = itchat.originInstance.loginInfo
for i in itchat.loginInfo:
    debug(i, itchat.loginInfo[i])
itchat.run(debug=debugState)
