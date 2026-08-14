#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Forex Data Downloader - جلب بيانات الفوركس الحقيقية
تحميل سنة كاملة من بيانات الفوركس للاختبار
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import json

class ForexDataDownloader:
    def __init__(self, data_dir='forex_data'):
        self.data_dir = data_dir
        self.currency_pairs = [
            'EURUSD=X',  # Euro/US Dollar
            'GBPUSD=X',  # British Pound/US Dollar
            'USDCHF=X',  # US Dollar/Swiss Franc
            'USDJPY=X',  # US Dollar/Japanese Yen
            'AUDUSD=X',  # Australian Dollar/US Dollar
            'USDCAD=X',  # US Dollar/Canadian Dollar
            'EURCHF=X',  # Euro/Swiss Franc
            'EURGBP=X',  # Euro/British Pound
            'EURJPY=X'   # Euro/Japanese Yen
        ]
        
        # إنشاء مجلد البيانات إذا لم يكن موجوداً
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def download_yearly_data(self, year=2024, timeframe='1h'):
        """
        تحميل بيانات سنة كاملة بفاصل ساعي (H1)
        year: السنة المطلوبة
        timeframe: الفاصل الزمني (1h للساعة)
        """
        print(f"\n🔄 جاري تحميل بيانات سنة {year}...\n")
        
        start_date = f'{year}-01-01'
        end_date = f'{year}-12-31'
        
        data_summary = {}
        
        for pair in self.currency_pairs:
            try:
                print(f"  📊 تحميل {pair.replace('=X', '')}...", end=' ')
                
                # تحميل البيانات
                df = yf.download(
                    pair,
                    start=start_date,
                    end=end_date,
                    interval=timeframe,
                    progress=False
                )
                
                if len(df) == 0:
                    print(f"❌ لا توجد بيانات")
                    continue
                
                # تنظيف البيانات
                df = df.dropna()
                df['Pair'] = pair.replace('=X', '')
                
                # حفظ البيانات
                filename = os.path.join(self.data_dir, f"{pair.replace('=X', '')}_H1_{year}.csv")
                df.to_csv(filename)
                
                data_summary[pair.replace('=X', '')] = {
                    'rows': len(df),
                    'start_date': str(df.index[0]),
                    'end_date': str(df.index[-1]),
                    'file': filename
                }
                
                print(f"✅ ({len(df)} ساعة)")
                
            except Exception as e:
                print(f"❌ خطأ: {str(e)}")
        
        # حفظ ملخص البيانات
        summary_file = os.path.join(self.data_dir, f'data_summary_{year}.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(data_summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ تم حفظ ملخص البيانات في: {summary_file}")
        return data_summary
    
    def get_data(self, pair, year=2024):
        """
        الحصول على بيانات زوج معين
        """
        filename = os.path.join(self.data_dir, f"{pair}_H1_{year}.csv")
        if os.path.exists(filename):
            return pd.read_csv(filename, index_col=0, parse_dates=True)
        return None


if __name__ == "__main__":
    # تحميل البيانات
    downloader = ForexDataDownloader()
    summary = downloader.download_yearly_data(year=2024)
    
    print("\n" + "="*60)
    print("📈 ملخص البيانات المحملة:")
    print("="*60)
    for pair, info in summary.items():
        print(f"\n{pair}:")
        print(f"  • عدد البيانات: {info['rows']} ساعة")
        print(f"  • من: {info['start_date'][:10]}")
        print(f"  • إلى: {info['end_date'][:10]}")
