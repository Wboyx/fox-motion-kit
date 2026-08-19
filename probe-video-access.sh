#!/usr/bin/env bash
# =====================================================================
# بررسی دسترسی به سرویس‌های ویدیو — فقط خواندنی
# هیچ حسابی نمی‌سازد، هیچ کلیدی نمی‌خواهد، فقط دسترسی شبکه را می‌سنجد.
#
# کد 000 یعنی TLS کامل نشد، معمولاً یعنی دامنه از این شبکه بسته است.
# =====================================================================
set -u
T=8
probe() {
  printf "  %-28s " "$1"
  curl -s -o /dev/null --max-time $T \
    -w "code=%{http_code} tls=%{time_appconnect}s total=%{time_total}s\n" "$2" 2>/dev/null \
    || echo "code=000 (fail)"
}
echo "زمان: $(date -u '+%Y-%m-%d %H:%M UTC')"
echo
echo "── سرویس‌های تولید ویدیو ──"
probe "Kling"            "https://app.klingai.com/"
probe "Runway"           "https://runwayml.com/"
probe "Luma"             "https://lumalabs.ai/"
probe "Pika"             "https://pika.art/"
probe "Hailuo / MiniMax" "https://hailuoai.video/"
probe "Vidu"             "https://www.vidu.com/"
probe "Google AI Studio" "https://aistudio.google.com/"
echo
echo "── مسیرهای متن‌باز و محلی ──"
probe "Hugging Face"     "https://huggingface.co/"
probe "GitHub raw"       "https://raw.githubusercontent.com/"
probe "ComfyUI repo"     "https://github.com/comfyanonymous/ComfyUI"
echo
echo "── ابزار محلی ──"
for c in ffmpeg ffprobe python3; do
  printf "  %-28s %s\n" "$c" "$(command -v $c || echo 'نصب نیست')"
done
echo
echo "راهنما:"
echo "  code=200 یا 3xx  -> باز و قابل استفاده"
echo "  code=000         -> بسته یا نیازمند مسیر دیگر"
echo "  اگر همه بسته بودند، مسیر ریگ دوبعدی و اجرای محلی گزینه امن است."
