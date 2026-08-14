#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام الاختبار الخلفي متعدد السنوات لبيانات الفوركس الحقيقية (2020 - 2026) - نسخة فائقة السرعة ودقيقة
يقوم بتحميل بيانات يومية حقيقية من Yahoo Finance لـ 9 أزواج عملات،
ويقوم بالتحسين وإيجاد أفضل الإعدادات الاحترافية لكل زوج في ثوانٍ معدودة.
"""

import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from itertools import product

class MultiYearRealBacktester:
    def __init__(self, data_dir='backtesting/forex_data', results_dir='backtesting/results'):
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.pairs = [
            'EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY',
            'AUDUSD', 'USDCAD', 'EURCHF', 'EURGBP', 'EURJPY'
        ]

        # إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)

    def download_real_data(self, start_date='2020-01-01', end_date='2026-08-14'):
        """
        تحميل بيانات الأسعار الحقيقية من Yahoo Finance لـ 9 أزواج عملات
        """
        print(f"\n🔄 جاري تحميل البيانات الحقيقية من {start_date} إلى {end_date}...")

        download_summary = {}
        for pair in self.pairs:
            ticker = f"{pair}=X"
            filename = os.path.join(self.data_dir, f"{pair}_D1_2020_2026.csv")

            # إذا كان الملف موجوداً مسبقاً، تخطي التحميل إلا إذا لزم الأمر
            if os.path.exists(filename):
                print(f"   • {pair}: الملف موجود مسبقاً محلياً.")
                df = pd.read_csv(filename, index_col=0, parse_dates=True)
                download_summary[pair] = len(df)
                continue

            print(f"   • جاري تحميل {pair} من Yahoo Finance...", end=' ')
            try:
                df = yf.download(ticker, start=start_date, end=end_date, interval='1d', progress=False)
                if df.empty:
                    print("❌ لا توجد بيانات!")
                    continue

                # تنظيف وتنظيم الأعمدة لإزالة المستويات المتعددة (Multi-index) إن وجدت في الإصدارات الجديدة من pandas/yfinance
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df = df.dropna()
                df.to_csv(filename)
                print(f"✅ تم تحميل {len(df)} يوم تداول وحفظه بنجاح.")
                download_summary[pair] = len(df)
            except Exception as e:
                print(f"❌ خطأ أثناء التحميل: {str(e)}")

        return download_summary

    def calculate_indicators(self, df):
        """
        حساب المؤشرات الفنية (RSI, MACD, Bollinger Bands)
        """
        df = df.copy()

        # 1. RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        # تجنب القسمة على الصفر
        loss = loss.replace(0, 1e-10)
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 2. MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # 3. Bollinger Bands
        df['BB_Mid'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)

        return df.dropna()

    def run_backtest_fast(self, pair, df, settings):
        """
        تشغيل محاكاة الاختبار الخلفي السريع في الذاكرة
        """
        balance = settings['initial_balance']
        position = None
        entry_price = 0
        trades_count = 0
        winning_trades = 0
        losing_trades = 0
        max_balance = balance
        min_balance = balance
        trades_list = []

        # تحديد قيمة النقطة (Pip) للزوج
        point = 0.01 if 'JPY' in pair else 0.0001

        # استخراج مصفوفات NumPy لتسريع التكرار بشكل فائق
        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        rsis = df['RSI'].values
        macd_hists = df['MACD_Histogram'].values
        dates = df.index

        # محاكاة التداول
        for i in range(1, len(df)):
            close_price = closes[i]
            high_price = highs[i]
            low_price = lows[i]
            rsi = rsis[i]
            macd_hist = macd_hists[i]
            prev_macd_hist = macd_hists[i-1]
            date_str = str(dates[i])[:10]

            # إدارة الصفقة المفتوحة
            if position is not None:
                tp_pips = settings['tp_pips']
                sl_pips = settings['sl_pips']
                lot_size = settings['lot_size']

                # حساب الربح/الخسارة بالقيمة المعيارية الموحدة لجميع الأزواج
                # كل 1 لوت كامل يعطي 10 دولار لكل نقطة ربح أو خسارة (تقريب قياسي دقيق ومثالي)
                pip_value_usd = lot_size * 10.0

                if position == 'buy':
                    tp_price = entry_price + (tp_pips * point)
                    sl_price = entry_price - (sl_pips * point)

                    # فحص وقف الخسارة
                    if low_price <= sl_price:
                        loss = pip_value_usd * sl_pips
                        balance -= loss
                        losing_trades += 1
                        trades_list.append({
                            'date': date_str,
                            'type': 'BUY',
                            'entry': entry_price,
                            'exit': sl_price,
                            'pips': -sl_pips,
                            'result': 'LOSS'
                        })
                        position = None

                    # فحص أخذ الربح
                    elif high_price >= tp_price and position is not None:
                        profit = pip_value_usd * tp_pips
                        balance += profit
                        winning_trades += 1
                        trades_list.append({
                            'date': date_str,
                            'type': 'BUY',
                            'entry': entry_price,
                            'exit': tp_price,
                            'pips': tp_pips,
                            'result': 'WIN'
                        })
                        position = None

                elif position == 'sell':
                    tp_price = entry_price - (tp_pips * point)
                    sl_price = entry_price + (sl_pips * point)

                    # فحص وقف الخسارة
                    if high_price >= sl_price:
                        loss = pip_value_usd * sl_pips
                        balance -= loss
                        losing_trades += 1
                        trades_list.append({
                            'date': date_str,
                            'type': 'SELL',
                            'entry': entry_price,
                            'exit': sl_price,
                            'pips': -sl_pips,
                            'result': 'LOSS'
                        })
                        position = None

                    # فحص أخذ الربح
                    elif low_price <= tp_price and position is not None:
                        profit = pip_value_usd * tp_pips
                        balance += profit
                        winning_trades += 1
                        trades_list.append({
                            'date': date_str,
                            'type': 'SELL',
                            'entry': entry_price,
                            'exit': tp_price,
                            'pips': tp_pips,
                            'result': 'WIN'
                        })
                        position = None

            # إشارات الدخول الفنية
            if position is None:
                # شراء: RSI منخفض وتحول MACD للإيجابية
                if rsi < settings['rsi_oversold'] and macd_hist > 0 and prev_macd_hist <= 0:
                    position = 'buy'
                    entry_price = close_price
                    trades_count += 1

                # بيع: RSI مرتفع وتحول MACD للسلبية
                elif rsi > settings['rsi_overbought'] and macd_hist < 0 and prev_macd_hist >= 0:
                    position = 'sell'
                    entry_price = close_price
                    trades_count += 1

            # تتبع الرصيد الأقصى والأدنى لحساب التراجع (Drawdown)
            max_balance = max(max_balance, balance)
            min_balance = min(min_balance, balance)

            # إذا تراجع الرصيد بشكل حاد وتجاوز النسبة القصوى المسموحة
            dd_percent = ((max_balance - balance) / max_balance) * 100
            if dd_percent > settings['max_dd_percent']:
                break

        # حساب إحصائيات الأداء الكلية
        profit_loss = balance - settings['initial_balance']
        roi = (profit_loss / settings['initial_balance']) * 100
        max_dd = ((max_balance - min_balance) / max_balance) * 100 if max_balance > 0 else 0
        win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0

        return {
            'pair': pair,
            'initial_balance': settings['initial_balance'],
            'final_balance': round(balance, 2),
            'profit_loss': round(profit_loss, 2),
            'roi_percent': round(roi, 2),
            'total_trades': trades_count,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_percent': round(win_rate, 2),
            'max_drawdown_percent': round(max_dd, 2),
            'settings': settings,
            'trades_sample': trades_list[:10]
        }

    def optimize_pair(self, pair, num_combinations=150):
        """
        تحسين الإعدادات لزوج معين للعثور على أفضل توليفة أداء
        """
        print(f"⚙️ جاري تحسين إعدادات {pair}...", end=' ')
        filename = os.path.join(self.data_dir, f"{pair}_D1_2020_2026.csv")
        if not os.path.exists(filename):
            print("❌ ملف البيانات غير موجود!")
            return None

        df_raw = pd.read_csv(filename, index_col=0, parse_dates=True)
        df = self.calculate_indicators(df_raw)

        # نطاق الإعدادات التي سيتم اختبارها للحصول على صفقات جيدة وأرباح آمنة وممتازة
        tp_range = [30, 50, 75, 100, 150, 200]
        sl_range = [60, 100, 150, 200, 250, 300]
        rsi_oversold_range = [25, 30, 35, 40, 45]
        rsi_overbought_range = [55, 60, 65, 70, 75]

        best_result = None
        best_score = -999999

        tested = 0
        for tp, sl, rsi_os, rsi_ob in product(tp_range, sl_range, rsi_oversold_range, rsi_overbought_range):
            if tested >= num_combinations:
                break

            # استبعاد المجموعات غير المتناسبة فنيًا
            if tp >= sl or rsi_os >= rsi_ob:
                continue

            settings = {
                'initial_balance': 10000, # رصيد أولي كبير كحساب احترافي
                'lot_size': 0.1,
                'tp_pips': tp,
                'sl_pips': sl,
                'max_dd_percent': 30.0,
                'rsi_oversold': rsi_os,
                'rsi_overbought': rsi_ob
            }

            res = self.run_backtest_fast(pair, df, settings)
            if res and res['total_trades'] >= 5:
                # حساب درجة التقييم (نظام النقاط الاحترافي)
                # درجات الربح، تراجع منخفض، ومعدل ربح مرتفع
                score = (res['roi_percent'] * 1.5) + (res['win_rate_percent'] * 1.0) - (res['max_drawdown_percent'] * 2.0)

                if score > best_score:
                    best_score = score
                    best_result = res

                tested += 1

        # إذا لم نجد أي إعدادات مناسبة بها صفقات، نأخذ الإعدادات الافتراضية
        if best_result is None:
            default_settings = {
                'initial_balance': 10000,
                'lot_size': 0.1,
                'tp_pips': 50,
                'sl_pips': 100,
                'max_dd_percent': 30.0,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            best_result = self.run_backtest_fast(pair, df, default_settings)

        print(f"✅ تم العثور على أفضل الإعدادات.")
        return best_result

    def run_comprehensive_system(self):
        """
        تشغيل النظام الشامل ببيانات حقيقية 2020 - 2026 لجميع الأزواج
        """
        # 1. تحميل البيانات
        self.download_real_data()

        # 2. تحسين واختبار جميع الأزواج
        all_pair_results = {}
        print("\n" + "="*80)
        print("📊 جاري البدء في التحسين والاختبار لجميع الأزواج (2020 - 2026)")
        print("="*80 + "\n")

        for pair in self.pairs:
            res = self.optimize_pair(pair)
            if res:
                all_pair_results[pair] = res
                print(f"   📈 {pair} | الرصيد النهائي: ${res['final_balance']} | العائد: {res['roi_percent']}% | صفقات: {res['total_trades']} | نسبة الربح: {res['win_rate_percent']}% | التراجع: {res['max_drawdown_percent']}%")

        # 3. حفظ التقرير في ملف JSON
        output_file = os.path.join(self.results_dir, "multiyear_report_2020_2026.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'period': '2020-01-01 to 2026-08-14',
                'results': all_pair_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 تم حفظ تقرير النتائج الشامل بنجاح في: {output_file}")
        return all_pair_results

if __name__ == "__main__":
    backtester = MultiYearRealBacktester()
    backtester.run_comprehensive_system()
