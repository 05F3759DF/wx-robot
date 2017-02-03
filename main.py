import itchat
from itchat.content import TEXT, PICTURE
import threading
import pdb, os
import json
import configparser
from urllib import request, parse


configFile = 'default.config'
if os.path.exists('user.config'):
    configFile = 'user.config'
config = configparser.ConfigParser()
config.read(configFile)
robotUrl = config['tuling']['url']
robotKey = config['tuling']['key`']

debugState = 'DEBUG' in os.environ
def debug(*data):
    if debugState:
        print(data)

auto_reply_switch = True
auto_reply_pool = {}

def auto_reply(**msg):
    if not auto_reply_switch:
        return
    itchat.send('抱歉，我暂时无法回复，稍后我会联系您。[自动回复]', toUserName=msg['FromUserName'])
    auto_reply_pool.pop(msg['FromUserName'])

def auto_reply_smart(**msg):
    if not auto_reply_switch:
        return
    print(msg)
    data = {
        'key': robotKey,
        'info': msg['Text'][1:].strip(),
        'userid': msg['FromUserName']
    }
    data = parse.urlencode(data).encode()
    print(data)
    req = request.Request(url=robotUrl, data=data)
    res = request.urlopen(req)
    res = res.read().decode()
    res = json.loads(res)
    debug(res)
    if res['code'] == 100000:
        itchat.send(res['text'], toUserName=msg['FromUserName'])
    else:
        itchat.send('本宝宝拒绝服务。', toUserName=msg['FromUserName'])

@itchat.msg_register([TEXT])
def text_reply(msg):
    if msg['FromUserName'] == itchat.loginInfo['User']['UserName']:
        if msg['ToUserName'] == 'filehelper':
            global auto_reply_switch
            if msg['Text'] == '开始自动回复':
                auto_reply_switch = True
                itchat.send('自动回复：开启', msg['ToUserName'])
            elif msg['Text'] == '结束自动回复':
                auto_reply_switch = False
                itchat.send('自动回复：关闭', msg['ToUserName'])
        if auto_reply_switch and msg['ToUserName'] in auto_reply_pool:
            debug('replied')
            timer = auto_reply_pool[msg['ToUserName']]
            timer.cancel()
            auto_reply_pool.pop(msg['ToUserName'])
    elif auto_reply_switch:
        if msg['Text'].startswith('#'):
            auto_reply_smart(**msg)
        else:
            timer = threading.Timer(15, auto_reply, kwargs=msg)
            auto_reply_pool[msg['FromUserName']] = timer
            timer.start()

itchat.auto_login(True, enableCmdQR=2)
itchat.loginInfo = itchat.originInstance.loginInfo
for i in itchat.loginInfo:
    debug(i, itchat.loginInfo[i])
itchat.run(debug=debugState)
