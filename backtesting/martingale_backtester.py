#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Martingale Backtester - اختبار استراتيجية Martingale
اختبار المتداول الآلي على بيانات حقيقية
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from forex_data_downloader import ForexDataDownloader

class MartingaleBacktester:
    def __init__(self, data_dir='forex_data'):
        self.data_dir = data_dir
        self.downloader = ForexDataDownloader(data_dir)
        self.trades = []
        self.results = {}
    
    def calculate_rsi(self, data, period=14):
        """
        حساب مؤشر RSI (Relative Strength Index)
        """
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data, fast=12, slow=26, signal=9):
        """
        حساب مؤشر MACD
        """
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def calculate_bollinger_bands(self, data, period=20, std_dev=2):
        """
        حساب Bollinger Bands
        """
        sma = data['Close'].rolling(window=period).mean()
        std = data['Close'].rolling(window=std_dev).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        return sma, upper_band, lower_band
    
    def backtest(self, pair, year=2024, settings=None):
        """
        تشغيل الاختبار الخلفي للمتداول
        pair: زوج العملات (مثل EURUSD)
        year: السنة
        settings: الإعدادات المخصصة
        """
        
        # الإعدادات الافتراضية
        if settings is None:
            settings = {
                'initial_balance': 1000,      # الرصيد الأولي بالدولار
                'lot_size': 0.1,              # حجم اللوت
                'martingale_multiplier': 2,   # مضاعف Martingale
                'tp_pips': 50,               # Take Profit بالنقاط
                'sl_pips': 100,              # Stop Loss بالنقاط
                'max_dd_percent': 30,        # أقصى تراجع مسموح به
                'rsi_overbought': 70,        # RSI مشتري زيادة
                'rsi_oversold': 30,          # RSI بائع زيادة
                'use_martingale': True       # استخدام Martingale
            }
        
        # تحميل البيانات
        data = self.downloader.get_data(pair, year)
        if data is None:
            print(f"❌ لا توجد بيانات لـ {pair}")
            return None
        
        print(f"\n🔍 اختبار {pair} بالإعدادات:")
        print(f"   • الرصيد الأولي: ${settings['initial_balance']}")
        print(f"   • حجم اللوت: {settings['lot_size']}")
        print(f"   • TP: {settings['tp_pips']} نقطة | SL: {settings['sl_pips']} نقطة")
        
        # حساب المؤشرات
        data['RSI'] = self.calculate_rsi(data)
        data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = self.calculate_macd(data)
        data['BB_Mid'], data['BB_Upper'], data['BB_Lower'] = self.calculate_bollinger_bands(data)
        
        # متغيرات التتبع
        balance = settings['initial_balance']
        position = None
        entry_price = 0
        trades_count = 0
        winning_trades = 0
        losing_trades = 0
        max_balance = balance
        min_balance = balance
        trades_list = []
        
        # الحد الأدنى للعملات (Pips)
        point = 0.0001 if pair != 'USDJPY' else 0.01
        
        # المسح عبر البيانات
        for i in range(100, len(data)):
            row = data.iloc[i]
            prev_row = data.iloc[i-1]
            
            # تحديث الرصيد
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
                        'result': 'LOSS (SL)'
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
                        'result': 'LOSS (SL)'
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
                        'result': 'WIN (TP)'
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
                        'result': 'WIN (TP)'
                    })
                    position = None
            
            # إشارات الدخول
            if position is None and i > 0:
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
            
            # فحص التراجع القصوى
            dd_percent = ((max_balance - balance) / max_balance) * 100
            if dd_percent > settings['max_dd_percent']:
                break
        
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
            'trades_sample': trades_list[:10]  # أول 10 عمليات
        }
        
        self.results[pair] = result
        return result
    
    def print_results(self, result):
        """
        طباعة نتائج الاختبار بشكل جميل
        """
        print(f"\n{'='*70}")
        print(f"📊 نتائج الاختبار: {result['pair']} - {result['year']}")
        print(f"{'='*70}")
        print(f"\n💰 النتائج المالية:")
        print(f"   • الرصيد الأولي: ${result['initial_balance']}")
        print(f"   • الرصيد النهائي: ${result['final_balance']}")
        print(f"   • الربح/الخسارة: ${result['profit_loss']}")
        print(f"   • العائد (ROI): {result['roi_percent']}%")
        
        print(f"\n📈 إحصائيات التداول:")
        print(f"   • إجمالي العمليات: {result['total_trades']}")
        print(f"   • عمليات رابحة: {result['winning_trades']}")
        print(f"   • عمليات خاسرة: {result['losing_trades']}")
        print(f"   • معدل الفوز: {result['win_rate_percent']}%")
        
        print(f"\n⚠️ إدارة المخاطر:")
        print(f"   • أقصى تراجع: {result['max_drawdown_percent']}%")
        
        if result['trades_sample']:
            print(f"\n🎯 عينة من العمليات (أول 10):")
            for i, trade in enumerate(result['trades_sample'], 1):
                print(f"   {i}. {trade['type']:5} | Entry: {trade['entry']:.5f} | "
                      f"Exit: {trade['exit']:.5f} | {trade['pips']:+.0f} pips | {trade['result']}")
        
        print(f"\n{'='*70}\n")


if __name__ == "__main__":
    backtester = MartingaleBacktester()
    
    # اختبار زوج EURUSD بالإعدادات الافتراضية
    result = backtester.backtest('EURUSD', year=2024)
    if result:
        backtester.print_results(result)
