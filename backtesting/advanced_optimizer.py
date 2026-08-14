#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
محسّن متقدم - إيجاد أفضل الإعدادات
بحث شامل عن أفضل مجموعة إعدادات
"""

import numpy as np
import pandas as pd
from itertools import product
import json
from datetime import datetime
from standalone_backtester import StandaloneBacktester

class AdvancedOptimizer:
    """
    محسّن متقدم للعثور على أفضل الإعدادات
    """
    def __init__(self):
        self.backtester = StandaloneBacktester()
        self.optimization_results = []

    def optimize_pair(self, pair, year=2024, num_combinations=100):
        """
        تحسين الإعدادات لزوج معين
        """
        print(f"\
{'='*80}")
        print(f"⚙️ تحسين الإعدادات لـ {pair}")
        print(f"{'='*80}\
")

        # نطاقات الإعدادات المراد اختبارها
        tp_range = [20, 30, 40, 50, 60, 75, 100]              # Take Profit
        sl_range = [40, 60, 80, 100, 120, 150]               # Stop Loss
        rsi_oversold_range = [15, 20, 25, 30, 35]            # RSI Oversold
        rsi_overbought_range = [65, 70, 75, 80, 85]          # RSI Overbought

        results = []
        test_count = 0

        # اختبار المجموعات
        for tp, sl, rsi_os, rsi_ob in product(tp_range, sl_range, rsi_oversold_range, rsi_overbought_range):
            if test_count >= num_combinations:
                break

            # تخطي المجموعات غير المنطقية
            if tp >= sl or rsi_os >= rsi_ob:
                continue

            settings = {
                'initial_balance': 1000,
                'lot_size': 0.1,
                'tp_pips': tp,
                'sl_pips': sl,
                'max_dd_percent': 30,
                'rsi_overbought': rsi_ob,
                'rsi_oversold': rsi_os
            }

            result = self.backtester.backtest(pair, year, settings)

            if result:
                # حساب درجة الأداء
                score = self.calculate_score(result)
                result['score'] = score
                results.append(result)
                test_count += 1

                # عرض التقدم
                if test_count % 10 == 0:
                    print(f"   [✓] اختبار {test_count}/{num_combinations}")

        # ترتيب النتائج
        results.sort(key=lambda x: x['score'], reverse=True)
        self.optimization_results = results

        return results[:5]  # إرجاع أفضل 5

    def calculate_score(self, result):
        """
        حساب درجة الأداء الكلية
        الصيغة: (ROI × 0.4) + (Win Rate × 0.4) + (Safety × 0.2)
        """
        roi_score = min(max(result['roi_percent'], 0), 100)  # 0-100
        win_rate = result['win_rate_percent']  # 0-100

        # درجة الأمان (كلما قل التراجع = أفضل)
        safety_score = max(0, 100 - result['max_drawdown_percent'] * 2)

        # الحساب النهائي
        total_score = (roi_score * 0.4) + (win_rate * 0.4) + (safety_score * 0.2)

        return total_score

    def print_top_results(self, top_n=5):
        """
        طباعة أفضل النتائج
        """
        if not self.optimization_results:
            print("❌ لا توجد نتائج")
            return

        print(f"\
{'='*100}")
        print(f"🏆 أفضل {top_n} إعدادات")
        print(f"{'='*100}\
")

        for rank, result in enumerate(self.optimization_results[:top_n], 1):
            print(f"\
🥇 الترتيب #{rank} | درجة: {result['score']:.2f}/100")
            print(f"{'─'*100}")

            print(f"  ⚙️ الإعدادات:")
            print(f"     • TP: {result['settings']['tp_pips']:3d} pips  |  SL: {result['settings']['sl_pips']:3d} pips")
            print(f"     • RSI: {result['settings']['rsi_oversold']:2d}-{result['settings']['rsi_overbought']:2d}")

            print(f"\
  💰 النتائج المالية:")
            print(f"     • الربح: ${result['profit_loss']:.2f}  |  العائد: {result['roi_percent']:+.2f}%")

            print(f"\
  📊 إحصائيات التداول:")
            print(f"     • إجمالي العمليات: {result['total_trades']:3d}")
            print(f"     • معدل الفوز: {result['win_rate_percent']:.2f}% ({result['winning_trades']}/{result['total_trades']})")

            print(f"\
  ⚠️ المخاطر:")
            print(f"     • أقصى تراجع: {result['max_drawdown_percent']:.2f}%")

            # تقييم
            print(f"\
  📈 التقييم:")
            if result['roi_percent'] > 50:
                print(f"     ✅ العائد: ممتاز جداً")
            elif result['roi_percent'] > 20:
                print(f"     ✅ العائد: جيد جداً")
            elif result['roi_percent'] > 0:
                print(f"     ⚠️ العائد: مقبول")

            if result['win_rate_percent'] > 65:
                print(f"     ✅ معدل الفوز: ممتاز")
            elif result['win_rate_percent'] > 55:
                print(f"     ✅ معدل الفوز: جيد")

            if result['max_drawdown_percent'] < 15:
                print(f"     ✅ إدارة المخاطر: آمنة جداً")
            elif result['max_drawdown_percent'] < 25:
                print(f"     ⚠️ إدارة المخاطر: مقبولة")
            else:
                print(f"     🚨 إدارة المخاطر: عالية الخطورة")

    def create_final_recommendation(self):
        """
        إنشاء توصية نهائية
        """
        if not self.optimization_results:
            return None

        best = self.optimization_results[0]

        recommendation = {
            'timestamp': datetime.now().isoformat(),
            'best_settings': best['settings'],
            'expected_performance': {
                'roi_percent': best['roi_percent'],
                'win_rate_percent': best['win_rate_percent'],
                'max_drawdown_percent': best['max_drawdown_percent'],
                'score': best['score']
            },
            'quality_level': self._determine_quality(best),
            'recommendations': self._get_recommendations(best),
            'warnings': self._get_warnings(best)
        }

        return recommendation

    def _determine_quality(self, result):
        """
        تحديد مستوى الجودة
        """
        score = result['score']

        if score >= 75:
            return "🟢 ممتاز جداً"
        elif score >= 60:
            return "🟡 جيد"
        elif score >= 45:
            return "🟠 مقبول"
        else:
            return "🔴 ضعيف"

    def _get_recommendations(self, result):
        """
        الحصول على توصيات
        """
        recommendations = []

        if result['roi_percent'] > 30:
            recommendations.append("✅ العائد عالي جداً - يمكن الاستثمار برصيد كبير")
        elif result['roi_percent'] > 10:
            recommendations.append("✅ العائد جيد - مناسب للاستثمار المتوسط")

        if result['win_rate_percent'] > 65:
            recommendations.append("✅ معدل الفوز عالي - الاستراتيجية موثوقة")

        if result['max_drawdown_percent'] < 20:
            recommendations.append("✅ المخاطر منخفضة - آمن للتداول")

        if result['total_trades'] > 100:
            recommendations.append("✅ عدد العمليات كافي للإحصائيات")

        return recommendations

    def _get_warnings(self, result):
        """
        الحصول على تحذيرات
        """
        warnings = []

        if result['roi_percent'] < 0:
            warnings.append("🚨 الاستراتيجية خاسرة - لا تستخدمها بأموال حقيقية")

        if result['win_rate_percent'] < 50:
            warnings.append("⚠️ معدل الفوز أقل من 50% - عالية الخطورة")

        if result['max_drawdown_percent'] > 30:
            warnings.append("⚠️ التراجع الأقصى عالي - مخاطر عالية")

        if result['total_trades'] < 30:
            warnings.append("⚠️ عدد العمليات قليل - البيانات غير كافية")

        return warnings

    def export_optimization(self, filename='optimization_report.json'):
        """
        تصدير تقرير التحسين
        """
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.optimization_results),
            'top_5_results': []
        }

        for result in self.optimization_results[:5]:
            export_result = result.copy()
            export_result.pop('trades_sample', None)
            export_data['top_5_results'].append(export_result)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"\
✅ تم حفظ التقرير في: {filename}")

    def compare_settings(self, settings_list):
        """
        مقارنة عدة مجموعات إعدادات
        """
        print(f"\
{'='*100}")
        print("🔄 مقارنة الإعدادات")
        print(f"{'='*100}\
")

        comparison_results = []

        for settings in settings_list:
            result = self.backtester.backtest('EURUSD', settings=settings)
            comparison_results.append({
                'TP': settings['tp_pips'],
                'SL': settings['sl_pips'],
                'ROI%': f"{result['roi_percent']:.2f}%",
                'Win%': f"{result['win_rate_percent']:.2f}%",
                'Trades': result['total_trades'],
                'MaxDD%': f"{result['max_drawdown_percent']:.2f}%"
            })

        df = pd.DataFrame(comparison_results)
        print(df.to_string(index=False))
        print()


if __name__ == "__main__":
    print("\
" + "="*100)
    print("🎯 محسّن متقدم - البحث عن أفضل الإعدادات")
    print("="*100)

    optimizer = AdvancedOptimizer()

    # تحسين EURUSD
    top_results = optimizer.optimize_pair('EURUSD', year=2024, num_combinations=50)

    # عرض أفضل النتائج
    optimizer.print_top_results(top_n=5)

    # التوصية النهائية
    recommendation = optimizer.create_final_recommendation()

    if recommendation:
        print(f"\
{'='*100}")
        print("💡 التوصية النهائية")
        print(f"{'='*100}\
")
        print(f"مستوى الجودة: {recommendation['quality_level']}")
        print(f"\
الإعدادات الموصى بها:")
        for key, value in recommendation['best_settings'].items():
            print(f"   • {key}: {value}")

        if recommendation['recommendations']:
            print(f"\
✅ الإيجابيات:")
            for rec in recommendation['recommendations']:
                print(f"   {rec}")

        if recommendation['warnings']:
            print(f"\
⚠️ التحذيرات:")
            for warning in recommendation['warnings']:
                print(f"   {warning}")

    # حفظ التقرير
    optimizer.export_optimization('optimization_report.json')

    print(f"\
{'='*100}")
    print("✅ اكتمل التحسين بنجاح!")
    print(f"{'='*100}\
")
