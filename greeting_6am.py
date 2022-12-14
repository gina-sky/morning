from datetime import date, datetime, timedelta
import math
import sys
from wechatpy import WeChatClient, WeChatClientException, WeChatComponent
from wechatpy.client.api import WeChatMessage
from wechatpy.client import WeChatComponentClient
import requests
import os
import random
import json
import pickle
import time

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d") #今天的日期

start_date = os.getenv('START_DATE')
city = os.getenv('CITY')
birthday = os.getenv('BIRTHDAY')

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')

SYS_PATH = sys.path[0] + '/'
if app_id is None or app_secret is None:
  print('请设置 APP_ID 和 APP_SECRET')
  try:
    with open(SYS_PATH + 'greeting_6am.config', 'r') as f:
      datas = f.read()
      data_json = json.loads(datas)
      print(data_json)
      start_date = data_json['START_DATE']
      city = data_json['CITY']
      birthday = data_json['BIRTHDAY']
      app_id = data_json['APP_ID']
      app_secret = data_json['APP_SECRET']
      user_ids = data_json['USER_ID']
      template_id = data_json['TEMPLATE_ID']
  except Exception as e:
    print(e)
    exit(422)

if not user_ids:
  print('请设置 USER_ID,若存在多个 ID 用回车分开')
  exit(422)

if template_id is None:
  print('请设置 TEMPLATE_ID')
  exit(422)

# weather 直接返回对象，在使用的地方用字段进行调用。
CITY_SY = '邵阳'
CITY_WZ = '温州'
CITY_ZH = '珠海'
def get_weather(c):
  if c is None:
    print('请设置城市')
    return None
  url = "https://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + c
  res = requests.get(url).json()
  if res is None:
    return None
  weather = res['data']['list'][0]
  return weather

# 纪念日正数
def get_memorial_days_count():
  if start_date is None:
    print('没有设置 START_DATE')
    return 0
  delta = today - datetime.strptime(start_date, "%Y-%m-%d")
  return delta.days

# 生日倒计时
def get_birthday_left():
  if birthday is None:
    print('没有设置 BIRTHDAY')
    return 0
  next = datetime.strptime(str(today.year) + "-" + birthday, "%Y-%m-%d")
  if next < nowtime:
    next = next.replace(year=next.year + 1)
  return (next - today).days

# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
CHP_URL = "https://api.shadiao.pro/chp"
DU_URL = "https://api.shadiao.pro/du"
def get_words(url):
  words = requests.get(url)
  if words.status_code != 200:
    return get_words()
  return words.json()['data']['text']

# https://api.shadiao.pro/du

def format_temperature(temperature):
  return math.floor(temperature)

# 随机颜色
def get_random_color():
  return "#%06x" % random.randint(0, 0xFFFFFF)

class Data_token():
  def __init__(self, client, expire) -> None:
    self.client = client
    self.expire = expire

def save_client_data(file, obj):
  with open(file, 'wb') as f:
    f.write(pickle.dumps(obj))
    # pickle.dump(obj, f)

def load_client_data(file):
  obj = None
  try:
    with open(file, 'rb') as f:
      obj = pickle.loads(f.read())
      # obj = pickle.load(f)
  except Exception as e:
    print(e)
  return obj

# def check_client_token_expire(client):
#   pass


# def get_client(app_id, app_secret):
#   client = None
#   try:
#     client = WeChatClient(app_id, app_secret)
#   except WeChatClientException as e:
#     print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
#     exit(502)
#   # print("client" )
#   # print(dict(client))
#   # client.expires_at
#   # client.access_token

# return client``


TOAKEN_FILE = SYS_PATH + 'token.dat'

def get_client(app_id, app_secret):
  
  da_token = load_client_data(TOAKEN_FILE) 
  now = int(time.time())
  client = None
  expire = None
  if da_token is not None:
    client = getattr(da_token, 'client')
    expire = getattr(da_token, 'expire')
  
  if (client is None) or (expire <= now):
    try:
      client = WeChatClient(app_id, app_secret)

      da_token = Data_token(client, now + 7200)
      save_client_data(TOAKEN_FILE, da_token)
    except WeChatClientException as e:
      print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
      exit(502)
  else:
    print("use saved token")
 
  return client

def get_weather_ntimes(city, n=0):
  w = get_weather(city)
  n = n + 1
  if n >= 10:
    print('获取天气失败')
    exit(422)
  if w is None:
    print(n)
    return get_weather_ntimes(city, n)
  else:
    return w

def get_wemessage(client):
  wm = WeChatMessage(client)
  # citys = [CITY_SY, CITY_WZ, CITY_ZH]
  weather = get_weather_ntimes(CITY_SY)
  weather_wz = get_weather_ntimes(CITY_WZ)
  weather_zh = get_weather_ntimes(CITY_ZH)
  # if weather is None:
  #   print('获取天气失败')
  #   exit(422)
  data = {
    "city": {
      "value": CITY_SY,
      "color": get_random_color()
    },
    "date": {
      "value": today.strftime('%Y年%m月%d日'),
      "color": get_random_color()
    },
    "weather": {
      "value": weather['weather'],
      "color": get_random_color()
    },
    "temperature": {
      "value": math.floor(weather['temp']),
      "color": get_random_color()
    },
    "highest": {
      "value": math.floor(weather['high']),
      "color": get_random_color()
    },
    "lowest": {
      "value": math.floor(weather['low']),
      "color": get_random_color()
    },
    "airquality": {
      "value": weather['airQuality'],
      "color": get_random_color()
    },

    "city_wz": {
      "value": CITY_WZ,
      "color": get_random_color()
    },
    "weather_wz": {
      "value": weather_wz['weather'],
      "color": get_random_color()
    },
    "temperature_wz": {
      "value": math.floor(weather_wz['temp']),
      "color": get_random_color()
    },
    "highest_wz": {
      "value": math.floor(weather_wz['high']),
      "color": get_random_color()
    },
    "lowest_wz": {
      "value": math.floor(weather_wz['low']),
      "color": get_random_color()
    },
    "airquality_wz": {
      "value": weather_wz['airQuality'],
      "color": get_random_color()
    },

    "city_zh": {
      "value": CITY_ZH,
      "color": get_random_color()
    },
    "weather_zh": {
      "value": weather_zh['weather'],
      "color": get_random_color()
    },
    "temperature_zh": {
      "value": math.floor(weather_zh['temp']),
      "color": get_random_color()
    },
    "highest_zh": {
      "value": math.floor(weather_zh['high']),
      "color": get_random_color()
    },
    "lowest_zh": {
      "value": math.floor(weather_zh['low']),
      "color": get_random_color()
    },
    "airquality_zh": {
      "value": weather_zh['airQuality'],
      "color": get_random_color()
    },


    "love_days": {
      "value": get_memorial_days_count(),
      "color": get_random_color()
    },
    "birthday_left": {
      "value": get_birthday_left(),
      "color": get_random_color()
    },
    "jokes_chp": {
      "value": get_words(CHP_URL),
      "color": get_random_color()
    },
    "jokes_cold": {
      "value": get_words(DU_URL),
      "color": get_random_color()
    },
  }
  return wm, data

# wm = WeChatMessage(client)
# weather = get_weather(CITY_SY)
# if weather is None:
#   print('获取天气失败')
#   exit(422)
# data = {
#   "city": {
#     "value": city,
#     "color": get_random_color()
#   },
#   "date": {
#     "value": today.strftime('%Y年%m月%d日'),
#     "color": get_random_color()
#   },
#   "weather": {
#     "value": weather['weather'],
#     "color": get_random_color()
#   },
#   "temperature": {
#     "value": math.floor(weather['temp']),
#     "color": get_random_color()
#   },
#   "highest": {
#     "value": math.floor(weather['high']),
#     "color": get_random_color()
#   },
#   "lowest": {
#     "value": math.floor(weather['low']),
#     "color": get_random_color()
#   },
#   "love_days": {
#     "value": get_memorial_days_count(),
#     "color": get_random_color()
#   },
#   "birthday_left": {
#     "value": get_birthday_left(),
#     "color": get_random_color()
#   },
#   "jokes_chp": {
#     "value": get_words(CHP_URL),
#     "color": get_random_color()
#   },
#   "jokes_cold": {
#     "value": get_words(DU_URL),
#     "color": get_random_color()
#   },
# }

if __name__ == '__main__':
  client = get_client(app_id, app_secret)
  wm, data = get_wemessage(client)
  print(data)
  count = 0
  try:
    for user_id in user_ids:
      res = wm.send_template(user_id, template_id, data)
      count+=1
  except WeChatClientException as e:
    print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
    exit(502)

  print("发送了" + str(count) + "条消息")