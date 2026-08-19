# 🎞 Fox Motion Kit

بازوی عملیاتی فاکسی ۶. شیت را می‌گیرد، پلان می‌سازد، خروجی را می‌سنجد و می‌چیند.

## چرا

قانون خانواده فاکسی: **لایه ایمنی در کد باشد، نه در پرامپت.** ثبات، حسابداری و ممیزی نباید به حافظه سپرده شود.

## نصب

```bash
git clone https://github.com/Wboyx/fox-motion-kit.git
cd <پوشه پروژه ویدیو>
python3 /path/to/fox-motion-kit/motion.py init "نام پروژه"
```

بدون هیچ کتابخانه بیرونی. فقط پایتون ۳. برای بررسی عددی و چیدمان، `ffmpeg` لازم است.

## گردش کار

```bash
motion.py init "fam-ep01" --aspect 9:16 --resolution 1080x1920 --fps 30 --route rig
motion.py char add mehti --prompt-name MEHTI --desc "..." --sheet sheets/mehti_sheet.png --trait "glasses always on"
motion.py shot add --char mehti --motion "waves at camera and smiles" --camera "medium close-up, static" --duration 4
motion.py prompt --id s01
motion.py log s01 --model kling-3.0 --result approved --cost 0.4
motion.py qa --frames
motion.py assemble --audio motion/audio/ep01.wav
motion.py status
```

## چه چیزی را خودکار می‌گیرد

```text
پرامپت شش‌جزئی استاندارد با سبک و ممنوعه‌های ثابت
هشدار وقتی پلان چند حرکت هم‌زمان دارد
هشدار وقتی مدت از ۸ ثانیه بیشتر است
هشدار وقتی کاراکتر مشخص نشده و هویت قفل نمی‌شود
بررسی عددی ابعاد، مدت و نرخ فریم خروجی
استخراج فریم اول و آخر برای مقایسه پیوستگی
دفتر تلاش‌ها: مدل، نتیجه، هزینه
```

## بررسی دسترسی

```bash
bash probe-video-access.sh
```

فقط خواندنی. نشان می‌دهد کدام سرویس از شبکه تو باز است. اگر همه بسته بودند، مسیر ریگ دوبعدی و اجرای محلی گزینه امن است.

## اسناد

```text
docs/MODELS.md      جدول مدل‌ها و قانون بازبینی دوره‌ای
docs/RIG_PATH.md    مسیر ریگ دوبعدی و دروازه پذیرش آن
tests/goldens_foxy6.md  مجموعه تست فاکسی ۶
```

## ساختار پروژه ویدیو

```text
motion/PROJECT.json    قالب، سبک، کاراکترها
motion/SHOTLIST.json   فهرست پلان‌ها و وضعیتشان
motion/LEDGER.json     دفتر تلاش‌ها و هزینه
motion/prompts/        پرامپت هر پلان
motion/keyframes/      فریم کلیدی
motion/shots/          کلیپ‌ها
motion/qa/             فریم اول و آخر برای مقایسه
motion/final/          خروجی نهایی
```
