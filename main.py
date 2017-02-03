import itchat
from itchat.content import TEXT, PICTURE
import threading
import pdb, os

debugState = 'DEBUG' in os.environ
def debug(*data):
    if 'DEBUG' in os.environ:
        print(data)

auto_reply_pool = {}

def auto_reply(**msg):
    itchat.send('抱歉，我暂时无法回复，稍后我会联系您。[自动回复]', toUserName=msg['FromUserName'])
    auto_reply_pool.pop(msg['FromUserName'])

@itchat.msg_register([TEXT])
def text_reply(msg):
    if msg['FromUserName'] == itchat.loginInfo['User']['UserName']:
        debug('replied')
        timer = auto_reply_pool[msg['ToUserName']]
        timer.cancel()
        auto_reply_pool.pop(msg['ToUserName'])
    else:
        timer = threading.Timer(15, auto_reply, kwargs=msg)
        auto_reply_pool[msg['FromUserName']] = timer
        timer.start()

itchat.auto_login(True, enableCmdQR=2)
itchat.loginInfo = itchat.originInstance.loginInfo
for i in itchat.loginInfo:
    print(i, itchat.loginInfo[i])
itchat.run(debug=debugState)
