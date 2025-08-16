
import pandas as pd
import ta
import ccxt
import time
from google.colab import drive
from telegram import Bot
import nest_asyncio
import asyncio
import os

# لتجنب خطأ asyncio في Colab
nest_asyncio.apply()

# 1. تثبيت المكتبات (نحن بحاجة لإعادة تثبيتها عند كل جلسة جديدة)
# Railway يقوم بتثبيت المكتبات تلقائيًا بناءً على ملف requirements.txt
# لذلك لا نحتاج لهذه الأوامر في الملف النهائي
# !pip install ccxt
# !pip install ta
# !pip install pandas
# !pip install numpy
# !pip install python-telegram-bot

# --- مفاتيحك الخاصة ---
# في بيئة Railway، يتم تخزين المفاتيح كمتغيرات بيئة (Environment Variables)
# وهذا يجعلها أكثر أمانًا
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
API_KEY = os.environ.get('API_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')

# --------------------------------
# الجزء الأول: إعداد البوت و التليجرام
# --------------------------------
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
})
bot = Bot(token=BOT_TOKEN)

# --------------------------------
# الجزء الثاني: دالة التشغيل الرئيسية
# --------------------------------
async def main_bot_loop():
    await bot.send_message(chat_id=CHAT_ID, text="البوت جاهز للعمل على Railway. سيبدأ بإرسال التقارير الآن.")
    
    while True:
        try:
            # 1. سحب البيانات اللحظية
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            # 2. إضافة المؤشرات الفنية
            df['RSI'] = ta.momentum.rsi(df['close'], window=14)
            df['MACD'] = ta.trend.macd_diff(df['close'])
            df['EMA_9'] = ta.trend.ema_indicator(df['close'], window=9)
            df['EMA_21'] = ta.trend.ema_indicator(df['close'], window=21)

            # 3. اتخاذ القرار
            last_row = df.iloc[-1]
            buy_signal = (last_row['RSI'] < 30) and (last_row['MACD'] > 0) and (last_row['EMA_9'] > last_row['EMA_21'])
            sell_signal = (last_row['RSI'] > 70) and (last_row['MACD'] < 0) and (last_row['EMA_9'] < last_row['EMA_21'])
            
            # 4. إرسال التقارير
            message = f"مرحباً! هذا تقرير جديد من البوت. 
"                       f"آخر سعر: {last_row['close']}$ 
"                       f"RSI: {last_row['RSI']:.2f} 
"                       f"MACD: {last_row['MACD']:.2f} 
"                       f"إشارة شراء: {'نعم' if buy_signal else 'لا'} 
"                       f"إشارة بيع: {'نعم' if sell_signal else 'لا'}"

            await bot.send_message(chat_id=CHAT_ID, text=message)
            
            # 5. تنفيذ الصفقات (في الحساب التجريبي)
            if buy_signal:
                # يمكنك إضافة كود الشراء هنا
                await bot.send_message(chat_id=CHAT_ID, text="🎉 إشارة شراء قوية! البوت قام بصفقة شراء.")
            elif sell_signal:
                # يمكنك إضافة كود البيع هنا
                await bot.send_message(chat_id=CHAT_ID, text="📉 إشارة بيع قوية! البوت قام بصفقة بيع.")

            print("تم إرسال التقرير بنجاح.")

            # 6. الانتظار قبل التحديث التالي (كل 15 دقيقة)
            await asyncio.sleep(15 * 60) # 15 دقيقة

        except Exception as e:
            print(f"حدث خطأ: {e}")
            await bot.send_message(chat_id=CHAT_ID, text=f"خطأ في البوت: {e}")
            await asyncio.sleep(60) # انتظار دقيقة قبل المحاولة مرة أخرى

async def start_bot():
    await main_bot_loop()

if __name__ == '__main__':
    asyncio.run(start_bot())
