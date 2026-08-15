# نظام الاختبار الخلفي للمتداول الآلي (Forex Hacked Pro Backtester)

## 📋 وصف النظام

نظام شامل لاختبار وتحسين المتداول الآلي "Forex Hacked Pro" على بيانات حقيقية من مختلف الأسواق والأصول المالية.

## 🎯 المميزات

✅ **جلب البيانات الحقيقية**: تحميل بيانات حقيقية للفوركس والأسواق المالية عبر Yahoo Finance

✅ **دعم متعدد الأصول (Multi-Asset)**:
   - **العملات الرقمية (Crypto)**: BTC-USD, ETH-USD, SOL-USD
   - **سوق العملات (Forex)**: EURUSD, GBPUSD, USDJPY وغيرها
   - **الأسهم الأمريكية (Stocks)**: AAPL, NVDA, TSLA, MSFT
   - **السلع والمعادن (Commodities)**: Gold, Silver, Crude Oil

✅ **محاكاة تنفيذ البروكر (Broker Execution Profiles)**:
   - ECN Raw Account (سبريد منخفض + عمولة)
   - Standard Account (سبريد معياري)
   - High Spread Account (سبريد مرتفع)

✅ **محاكاة دقيقة**: محاكاة الاستراتيجية مع ثلاث مؤشرات رئيسية:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands

✅ **إدارة المخاطر**: تتبع التراجع القصوى (Drawdown) والرصيد

✅ **تحسين الإعدادات**: اختبار مئات المجموعات للعثور على الأفضل

---

## 🚀 التشغيل والاختبار

### 1. التثبيت

```bash
cd backtesting
pip install -r requirements.txt
```

### 2. اختبار متعدد الأصول (Multi-Asset)

```bash
python3 multiasset_backtester.py
```

### 3. الاختبار الخلفي المستقل (Standalone)

```bash
python3 standalone_backtester.py
```

### 4. الاختبار متعدد السنوات للفوركس

```bash
python3 multiyear_real_backtester.py
```

---

## 📊 هيكل الملفات

```
backtesting/
├── multiasset_backtester.py     # اختبار متعدد الأصول (Crypto, Forex, Stocks, Commodities)
├── multiyear_real_backtester.py # اختبار متعدد السنوات لبيانات حقيقية (2020-2026)
├── standalone_backtester.py     # اختبار سريع مستقل
├── forex_data_downloader.py    # جلب البيانات
├── martingale_backtester.py    # محاكاة المتداول
├── optimizer.py                # تحسين الإعدادات
├── requirements.txt            # المكتبات المطلوبة
├── README.md                   # هذا الملف
└── forex_data/                 # مجلد البيانات المحملة
```

---

## ⚠️ تحذيرات مهمة

1. **الخسائر الممكنة**: التداول يتضمن مخاطرة عالية على رأس المال.

2. **البيانات التاريخية**: الاختبار على البيانات السابقة لا يضمن النتائج المستقبلية.

3. **اختبار على Demo أولاً**: اختبر على حساب تجريبي قبل استخدام أموال حقيقية.

---

**آخر تحديث**: أغسطس 2026
