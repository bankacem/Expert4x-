#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مختبر مستقل - لا يحتاج لتحميل البيانات من الإنترنت
يستخدم بيانات محاكاة واقعية جداً
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class RealisticDataGenerator:
    """
    توليد بيانات فوركس واقعية جداً تحاكي السلوك الفعلي
    """
    def __init__(self, seed=42):
        np.random.seed(seed)

    def generate_ohlc(self, pair, year=2024, num_days=365):
        """
        توليد بيانات OHLC واقعية
        """
        # الأسعار الافتتاحية التقريبية لكل زوج
        opening_prices = {
            'EURUSD': 1.0800,
            'GBPUSD': 1.2700,
            'USDCHF': 0.9200,
            'USDJPY': 110.50,
            'AUDUSD': 0.6700,
            'USDCAD': 1.3600,
            'EURCHF': 0.9900,
            'EURGBP': 0.8500,
            'EURJPY': 119.50
        }

        # التقلب اليومي لكل زوج (volatility)
        volatility = {
            'EURUSD': 0.008,
            'GBPUSD': 0.010,
            'USDCHF': 0.009,
            'USDJPY': 0.012,
            'AUDUSD': 0.011,
            'USDCAD': 0.009,
            'EURCHF': 0.008,
            'EURGBP': 0.009,
            'EURJPY': 0.011
        }

        start_price = opening_prices.get(pair, 1.0)
        daily_vol = volatility.get(pair, 0.01)

        # توليد البيانات
        dates = []
        closes = []
        current_price = start_price

        for day in range(num_days * 24):  # ساعة واحدة في كل حلقة
            # حركة عشوائية واقعية (Random Walk with Drift)
            drift = 0.0001
            shock = np.random.normal(0, daily_vol / 24)
            current_price *= (1 + drift/24 + shock)

            closes.append(current_price)

        # إنشاء DataFrame
        start_date = datetime(year, 1, 1)
        dates = [start_date + timedelta(hours=i) for i in range(len(closes))]

        df = pd.DataFrame({
            'Date': dates,
            'Close': closes
        })

        # توليد OHLC من Close
        df['High'] = df['Close'] * (1 + abs(np.random.normal(0, 0.005, len(df))))
        df['Low'] = df['Close'] * (1 - abs(np.random.normal(0, 0.005, len(df))))
        df['Open'] = df['Close'].shift(1).fillna(df['Close'].iloc[0])
        df['Volume'] = np.random.randint(1000, 10000, len(df))

        df.set_index('Date', inplace=True)

        return df[['Open', 'High', 'Low', 'Close', 'Volume']]


class StandaloneBacktester:
    """
    مختبر مستقل بدون الحاجة لتحميل بيانات خارجية
    """
    def __init__(self):
        self.data_generator = RealisticDataGenerator()
        self.results = {}

    def calculate_indicators(self, df):
        """
        حساب المؤشرات الفنية
        """
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        # Bollinger Bands
        df['BB_Mid'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)

        return df

    def backtest(self, pair, year=2024, settings=None):
        """
        تشغيل الاختبار الخلفي
        """
        if settings is None:
            settings = {
                'initial_balance': 1000,
                'lot_size': 0.1,
                'tp_pips': 50,
                'sl_pips': 100,
                'max_dd_percent': 30,
                'rsi_overbought': 70,
                'rsi_oversold': 30
            }

        print(f"\
🔄 توليد البيانات لـ {pair}...", end='')
        df = self.data_generator.generate_ohlc(pair, year)
        print(" ✅")

        print(f"📊 حساب المؤشرات...", end='')
        df = self.calculate_indicators(df)
        print(" ✅")

        print(f"⚙️ تشغيل المحاكاة...", end='')

        balance = settings['initial_balance']
        position = None
        entry_price = 0
        trades_count = 0
        winning_trades = 0
        losing_trades = 0
        max_balance = balance
        min_balance = balance
        trades_list = []

        point = 0.0001 if pair != 'USDJPY' else 0.01

        for i in range(100, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            if pd.isna(row['RSI']) or pd.isna(row['MACD_Histogram']):
                continue

            # إدارة الموضع الحالي
            if position is not None:
                current_price = row['Close']
                pips = (current_price - entry_price) / point

                # فحص Stop Loss
                if position == 'buy' and pips < -settings['sl_pips']:
                    loss = settings['lot_size'] * 100000 * settings['sl_pips'] * point
                    balance -= loss
                    losing_trades += 1
                    trades_list.append({
                        'type': 'BUY',
                        'entry': entry_price,
                        'exit': current_price,
                        'pips': -settings['sl_pips'],
                        'result': 'LOSS'
                    })
                    position = None

                elif position == 'sell' and pips > settings['sl_pips']:
                    loss = settings['lot_size'] * 100000 * settings['sl_pips'] * point
                    balance -= loss
                    losing_trades += 1
                    trades_list.append({
                        'type': 'SELL',
                        'entry': entry_price,
                        'exit': current_price,
                        'pips': -settings['sl_pips'],
                        'result': 'LOSS'
                    })
                    position = None

                # فحص Take Profit
                elif position == 'buy' and pips >= settings['tp_pips']:
                    profit = settings['lot_size'] * 100000 * settings['tp_pips'] * point
                    balance += profit
                    winning_trades += 1
                    trades_list.append({
                        'type': 'BUY',
                        'entry': entry_price,
                        'exit': current_price,
                        'pips': settings['tp_pips'],
                        'result': 'WIN'
                    })
                    position = None

                elif position == 'sell' and pips <= -settings['tp_pips']:
                    profit = settings['lot_size'] * 100000 * settings['tp_pips'] * point
                    balance += profit
                    winning_trades += 1
                    trades_list.append({
                        'type': 'SELL',
                        'entry': entry_price,
                        'exit': current_price,
                        'pips': settings['tp_pips'],
                        'result': 'WIN'
                    })
                    position = None

            # إشارات الدخول
            if position is None:
                rsi = row['RSI']
                macd_hist = row['MACD_Histogram']

                # شراء: RSI < 30 و MACD إيجابي
                if rsi < settings['rsi_oversold'] and macd_hist > 0 and prev_row['MACD_Histogram'] <= 0:
                    position = 'buy'
                    entry_price = row['Close']
                    trades_count += 1

                # بيع: RSI > 70 و MACD سلبي
                elif rsi > settings['rsi_overbought'] and macd_hist < 0 and prev_row['MACD_Histogram'] >= 0:
                    position = 'sell'
                    entry_price = row['Close']
                    trades_count += 1

            # تتبع الرصيد
            max_balance = max(max_balance, balance)
            min_balance = min(min_balance, balance)

            # فحص التراجع الأقصى
            dd_percent = ((max_balance - balance) / max_balance) * 100
            if dd_percent > settings['max_dd_percent']:
                break

        print(" ✅")

        # حساب الإحصائيات
        profit_loss = balance - settings['initial_balance']
        roi = (profit_loss / settings['initial_balance']) * 100
        max_dd = ((max_balance - min_balance) / max_balance) * 100
        win_rate = (winning_trades / trades_count * 100) if trades_count > 0 else 0

        result = {
            'pair': pair,
            'year': year,
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

        self.results[pair] = result
        return result

    def print_results(self, result):
        """
        طباعة النتائج بشكل جميل
        """
        print(f"\
{'='*80}")
        print(f"📊 نتائج الاختبار: {result['pair']} - {result['year']}")
        print(f"{'='*80}")

        print(f"\
💰 النتائج المالية:")
        print(f"   • الرصيد الأولي: ${result['initial_balance']}")
        print(f"   • الرصيد النهائي: ${result['final_balance']}")
        print(f"   • الربح/الخسارة: ${result['profit_loss']}")
        print(f"   • العائد (ROI): {result['roi_percent']}%")

        print(f"\
📈 إحصائيات التداول:")
        print(f"   • إجمالي العمليات: {result['total_trades']}")
        print(f"   • عمليات رابحة: {result['winning_trades']}")
        print(f"   • عمليات خاسرة: {result['losing_trades']}")
        print(f"   • معدل الفوز: {result['win_rate_percent']}%")

        print(f"\
⚠️ إدارة المخاطر:")
        print(f"   • أقصى تراجع: {result['max_drawdown_percent']}%")

        if result['trades_sample']:
            print(f"\
📋 عينة من العمليات (أول 10):")
            for i, trade in enumerate(result['trades_sample'], 1):
                emoji = '✅' if trade['result'] == 'WIN' else '❌'
                print(f"   {i}. {emoji} {trade['type']:5} | Entry: {trade['entry']:.5f} | "
                      f"Exit: {trade['exit']:.5f} | {trade['pips']:+.0f} pips")

        print(f"\
{'='*80}\
")

    def test_all_pairs(self, year=2024):
        """
        اختبار جميع الأزواج
        """
        pairs = [
            'EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY',
            'AUDUSD', 'USDCAD', 'EURCHF', 'EURGBP', 'EURJPY'
        ]

        print(f"\
{'='*80}")
        print(f"🌍 اختبار جميع أزواج العملات - {year}")
        print(f"{'='*80}")

        results_summary = []

        for pair in pairs:
            print(f"\
⏳ اختبار {pair}...")
            result = self.backtest(pair, year)
            self.print_results(result)

            results_summary.append({
                'Pair': pair,
                'Final Balance': f"${result['final_balance']}",
                'P&L': f"${result['profit_loss']}",
                'ROI %': f"{result['roi_percent']:.2f}%",
                'Trades': result['total_trades'],
                'Win Rate %': f"{result['win_rate_percent']:.2f}%",
                'Max DD %': f"{result['max_drawdown_percent']:.2f}%"
            })

        # طباعة الملخص
        self.print_summary(results_summary)
        return self.results

    def print_summary(self, results_summary):
        """
        طباعة ملخص النتائج
        """
        print(f"\
{'='*100}")
        print("📊 ملخص النتائج لجميع الأزواج")
        print(f"{'='*100}\
")

        df_summary = pd.DataFrame(results_summary)
        print(df_summary.to_string(index=False))

        # إحصائيات عامة
        total_pl = sum([float(r['P&L'].replace('$', '')) for r in results_summary])
        avg_wr = sum([float(r['Win Rate %'].replace('%', '')) for r in results_summary]) / len(results_summary)

        print(f"\
{'='*100}")
        print(f"🎯 الإحصائيات العامة:")
        print(f"   • إجمالي الربح/الخسارة: ${total_pl:.2f}")
        print(f"   • متوسط معدل الفوز: {avg_wr:.2f}%")
        print(f"   • عدد الأزواج المختبرة: {len(results_summary)}")
        print(f"{'='*100}\
")

    def export_results(self, filename='backtesting_results.json'):
        """
        تصدير النتائج
        """
        clean_results = {}
        for pair, result in self.results.items():
            clean = result.copy()
            clean.pop('trades_sample', None)
            clean_results[pair] = clean

        output = {
            'timestamp': datetime.now().isoformat(),
            'results': clean_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✅ تم حفظ النتائج في: {filename}")


if __name__ == "__main__":
    print("\
" + "="*80)
    print("🚀 نظام الاختبار الخلفي للمتداول الآلي")
    print("Forex Hacked Pro Backtesting System")
    print("="*80)

    backtester = StandaloneBacktester()

    # اختبار جميع الأزواج
    all_results = backtester.test_all_pairs(year=2024)

    # تصدير النتائج
    backtester.export_results('backtesting_results.json')

    print("\
✅ اكتمل الاختبار بنجاح!")
    print("📁 تحقق من ملف backtesting_results.json للنتائج المفصلة\
")
