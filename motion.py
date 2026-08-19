#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════
 FOX MOTION KIT — بازوی عملیاتی فاکسی ۶
 نسخه: 1.0  |  2026-08-19
════════════════════════════════════════════════════════════════

چه می‌کند:
  فهرست پلان می‌سازد، پرامپت استاندارد تولید می‌کند، هر تلاش را
  ثبت می‌کند، کیفیت خروجی را عددی می‌سنجد و پلان‌ها را می‌چیند.

چرا:
  ثبات و حسابداری نباید به حافظه سپرده شود. قانون خانواده:
  لایه ایمنی در کد باشد، نه در پرامپت.

چه نمی‌کند:
  هیچ تماسی با سرویس بیرونی نمی‌گیرد و هیچ کلیدی نمی‌خواهد.
  فقط فایل محلی می‌سازد و با ffmpeg کار می‌کند اگر نصب باشد.
"""

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

ROOT = os.getcwd()
MOTION = os.path.join(ROOT, "motion")
PROJECT = os.path.join(MOTION, "PROJECT.json")
SHOTS = os.path.join(MOTION, "SHOTLIST.json")
LEDGER = os.path.join(MOTION, "LEDGER.json")

C = {"b": "\033[1m", "g": "\033[32m", "y": "\033[33m",
     "r": "\033[31m", "c": "\033[36m", "d": "\033[2m", "x": "\033[0m"}

DEFAULT_STYLE = ("2D anime, cel shaded, flat colors, clean bold lineart, "
                 "hand-drawn look, consistent with reference")
DEFAULT_NEGATIVE = ("no text, no watermark, no extra characters, "
                    "no photorealistic skin, no style change, no morphing")


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        shutil.copy2(path, path + ".bak")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def have(cmd):
    return shutil.which(cmd) is not None


def need_project():
    p = load(PROJECT, None)
    if not p:
        print("پروژه ساخته نشده. اول این را بزن:\n  motion.py init \"نام پروژه\"")
        sys.exit(1)
    return p


# ───────────────────────────── init ─────────────────────────────

def cmd_init(a):
    if os.path.exists(PROJECT) and not a.force:
        print("پروژه از قبل هست. برای بازنویسی از --force استفاده کن.")
        return 1
    for d in ("shots", "keyframes", "prompts", "audio", "final", "qa"):
        os.makedirs(os.path.join(MOTION, d), exist_ok=True)
    proj = {
        "name": a.name,
        "created": now(),
        "aspect": a.aspect,
        "fps": a.fps,
        "resolution": a.resolution,
        "style_line": a.style or DEFAULT_STYLE,
        "negative": DEFAULT_NEGATIVE,
        "default_duration": a.duration,
        "route": a.route,
        "model": a.model or "انتخاب نشده",
        "characters": {},
    }
    save(PROJECT, proj)
    save(SHOTS, {"shots": []})
    save(LEDGER, {"entries": []})
    print("%sپروژه ساخته شد%s" % (C["g"], C["x"]))
    print("  مسیر     : %s" % MOTION)
    print("  نسبت     : %s   %s   %s fps" % (proj["aspect"], proj["resolution"], proj["fps"]))
    print("  مسیر تولید: %s" % proj["route"])
    print("\nقدم بعد:\n  motion.py char add <id> --desc \"...\" --sheet <path>")
    return 0


# ───────────────────────────── characters ─────────────────────────────

def cmd_char(a):
    proj = need_project()
    if a.action == "add":
        proj["characters"][a.id] = {
            "id": a.id,
            "name_in_prompt": (a.prompt_name or a.id).upper(),
            "desc": a.desc or "",
            "sheet": a.sheet or "",
            "locked_traits": a.trait or [],
        }
        save(PROJECT, proj)
        print("کاراکتر ثبت شد: %s" % a.id)
    elif a.action == "list":
        if not proj["characters"]:
            print("هیچ کاراکتری ثبت نشده.")
        for cid, c in proj["characters"].items():
            print("  %-10s %-14s شیت: %s" % (cid, c["name_in_prompt"], c["sheet"] or "—"))
            if c["desc"]:
                print("       %s" % c["desc"])
    return 0


# ───────────────────────────── shots ─────────────────────────────

def cmd_shot(a):
    proj = need_project()
    data = load(SHOTS, {"shots": []})
    if a.action == "add":
        sid = a.id or "s%02d" % (len(data["shots"]) + 1)
        if any(s["id"] == sid for s in data["shots"]):
            print("این شناسه از قبل هست: %s" % sid); return 1
        shot = {
            "id": sid,
            "char": a.char or "",
            "purpose": a.purpose or "",
            "motion": a.motion or "",
            "camera": a.camera or "static medium shot",
            "light": a.light or "soft natural light",
            "duration": a.duration or proj["default_duration"],
            "audio": a.audio or "",
            "status": "planned",
            "attempts": 0,
            "file": "",
            "created": now(),
        }
        data["shots"].append(shot)
        save(SHOTS, data)
        print("پلان اضافه شد: %s  (%s ثانیه)" % (sid, shot["duration"]))
        if not shot["motion"]:
            print("%sهشدار:%s حرکت خالی است. یک حرکت اصلی بنویس." % (C["y"], C["x"]))
    elif a.action == "list":
        print("\n%sفهرست پلان‌ها — %s%s\n" % (C["b"], proj["name"], C["x"]))
        if not data["shots"]:
            print("  خالی")
        total = 0
        for s in data["shots"]:
            icon = {"planned": "📝", "generated": "🎬", "approved": "✅",
                    "rejected": "❌"}.get(s["status"], "•")
            print("  %s %-6s %-10s %-38s %ss  تلاش:%d" %
                  (icon, s["id"], s["char"], (s["motion"] or s["purpose"])[:38],
                   s["duration"], s["attempts"]))
            total += float(s["duration"])
        print("\n  جمع: %d پلان، حدود %.0f ثانیه" % (len(data["shots"]), total))
    elif a.action == "set":
        for s in data["shots"]:
            if s["id"] == a.id:
                if a.status:
                    s["status"] = a.status
                if a.file:
                    s["file"] = a.file
                save(SHOTS, data)
                print("به‌روزرسانی شد: %s -> %s" % (a.id, s["status"]))
                return 0
        print("پلان پیدا نشد: %s" % a.id); return 1
    return 0


# ───────────────────────────── prompt ─────────────────────────────

def build_prompt(proj, shot):
    ch = proj["characters"].get(shot["char"], {})
    subject = ch.get("name_in_prompt", shot["char"] or "CHARACTER")
    desc = ch.get("desc", "")
    traits = ", ".join(ch.get("locked_traits", []))
    parts = [
        proj["style_line"] + ".",
        "%s%s%s %s." % (subject,
                        (" (" + desc + ")") if desc else "",
                        (" [" + traits + "]") if traits else "",
                        shot["motion"] or "stands still, subtle breathing"),
        shot["camera"] + ".",
        shot["light"] + ".",
        "Duration %s seconds, %s, %s fps." % (shot["duration"], proj["aspect"], proj["fps"]),
        proj["negative"] + ".",
    ]
    return "\n".join(parts)


def cmd_prompt(a):
    proj = need_project()
    data = load(SHOTS, {"shots": []})
    targets = [s for s in data["shots"] if (not a.id or s["id"] == a.id)]
    if not targets:
        print("پلانی پیدا نشد."); return 1
    for s in targets:
        text = build_prompt(proj, s)
        out = os.path.join(MOTION, "prompts", "%s.txt" % s["id"])
        with open(out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("\n%s── %s ──%s" % (C["c"], s["id"], C["x"]))
        print(text)
        print("%sذخیره شد: %s%s" % (C["d"], out, C["x"]))
        warns = []
        if s["motion"].count(" and ") >= 2:
            warns.append("چند حرکت هم‌زمان، پلان را بشکن")
        if float(s["duration"]) > 8:
            warns.append("مدت بیش از ۸ ثانیه، ریسک شکستن ثبات")
        if not s["char"]:
            warns.append("کاراکتر مشخص نشده، هویت قفل نمی‌شود")
        for w in warns:
            print("  %sهشدار:%s %s" % (C["y"], C["x"], w))
    return 0


# ───────────────────────────── ledger ─────────────────────────────

def cmd_log(a):
    load(PROJECT, None) or need_project()
    led = load(LEDGER, {"entries": []})
    led["entries"].append({
        "time": now(), "shot": a.shot, "model": a.model,
        "result": a.result, "note": a.note or "", "cost": a.cost or 0,
    })
    save(LEDGER, led)
    data = load(SHOTS, {"shots": []})
    for s in data["shots"]:
        if s["id"] == a.shot:
            s["attempts"] += 1
            if a.result == "approved":
                s["status"] = "approved"
            elif a.result == "rejected":
                s["status"] = "rejected"
            else:
                s["status"] = "generated"
            save(SHOTS, data)
    print("ثبت شد: %s / %s / %s" % (a.shot, a.model, a.result))
    return 0


# ───────────────────────────── qa ─────────────────────────────

def probe(path):
    if not have("ffprobe"):
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,r_frame_rate,duration,nb_frames",
             "-of", "json", path],
            capture_output=True, text=True, timeout=60)
        return json.loads(out.stdout)["streams"][0]
    except Exception:
        return None


def cmd_qa(a):
    proj = need_project()
    files = a.files or [os.path.join(MOTION, "shots", f)
                        for f in sorted(os.listdir(os.path.join(MOTION, "shots")))
                        if f.lower().endswith((".mp4", ".mov", ".webm"))]
    if not files:
        print("هیچ فایل ویدیویی پیدا نشد در motion/shots"); return 1
    if not have("ffprobe"):
        print("%sffprobe نصب نیست.%s برای بررسی عددی نصبش کن:" % (C["y"], C["x"]))
        print("  sudo apt install -y ffmpeg")
        print("بدون آن فقط چک‌لیست چشمی باقی می‌ماند.\n")
    want_w, want_h = (a.width, a.height) if a.width else (None, None)
    fails = 0
    for f in files:
        info = probe(f)
        line = "  %-28s " % os.path.basename(f)
        if not info:
            print(line + "%sبدون بررسی عددی%s" % (C["d"], C["x"]))
            continue
        w, h = info.get("width"), info.get("height")
        dur = float(info.get("duration") or 0)
        rate = info.get("r_frame_rate", "0/1")
        try:
            num, den = rate.split("/"); fps = round(float(num) / float(den), 2)
        except Exception:
            fps = 0
        issues = []
        if want_w and (w != want_w or h != want_h):
            issues.append("ابعاد %dx%d" % (w, h))
        if dur and (dur < 1 or dur > 12):
            issues.append("مدت %.1f ثانیه" % dur)
        if fps and abs(fps - float(proj["fps"])) > 1:
            issues.append("نرخ فریم %s" % fps)
        state = "%sOK%s" % (C["g"], C["x"]) if not issues else "%sبررسی%s" % (C["y"], C["x"])
        fails += 1 if issues else 0
        print(line + "%s  %dx%d  %.1fs  %sfps  %s" %
              (state, w or 0, h or 0, dur, fps, " | ".join(issues)))
        if a.frames and have("ffmpeg"):
            base = os.path.splitext(os.path.basename(f))[0]
            for tag, ts in (("first", "0"), ("last", str(max(dur - 0.1, 0)))):
                out = os.path.join(MOTION, "qa", "%s_%s.png" % (base, tag))
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", ts,
                                "-i", f, "-frames:v", "1", out],
                               capture_output=True, timeout=60)
            print("       فریم اول و آخر در motion/qa ذخیره شد")
    print("\n%s" % ("همه فایل‌ها در محدوده‌اند." if fails == 0
                    else "%d فایل نیاز به بررسی چشمی دارد." % fails))
    print("\n%sیادآوری دروازه QA فاکسی ۶:%s" % (C["c"], C["x"]))
    for i, t in enumerate([
        "هویت با شیت یکی است", "سبک دوبعدی حفظ شده", "فقط یک حرکت اصلی",
        "دست و صورت بدون بدشکلی", "بدون متن ناخواسته", "مدت و نسبت درست",
        "رنگ با پلان قبل هماهنگ", "بدون پرش و لرزش", "صدا هماهنگ",
        "تأیید صریح کاربر"], 1):
        print("  □ %2d. %s" % (i, t))
    return 0


# ───────────────────────────── assemble ─────────────────────────────

def cmd_assemble(a):
    proj = need_project()
    data = load(SHOTS, {"shots": []})
    approved = [s for s in data["shots"] if s["status"] == "approved" and s["file"]]
    if not approved:
        print("هیچ پلان تأییدشده‌ای با فایل ثبت‌نشده وجود ندارد.")
        print("اول: motion.py shot set <id> --status approved --file motion/shots/<file>")
        return 1
    listfile = os.path.join(MOTION, "concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for s in approved:
            p = s["file"] if os.path.isabs(s["file"]) else os.path.join(ROOT, s["file"])
            f.write("file '%s'\n" % p)
    out = a.out or os.path.join(MOTION, "final", "%s_v1.mp4" % proj["name"].replace(" ", "_"))
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile]
    if a.audio:
        cmd += ["-i", a.audio, "-c:v", "libx264", "-c:a", "aac", "-shortest"]
    else:
        cmd += ["-c:v", "libx264", "-an"]
    cmd += ["-pix_fmt", "yuv420p", "-r", str(proj["fps"]), out]
    print("پلان‌های تأییدشده: %d" % len(approved))
    print("فرمان چیدمان:\n  %s\n" % " ".join(cmd))
    if not have("ffmpeg"):
        print("%sffmpeg نصب نیست.%s نصب کن و همین فرمان را اجرا کن:" % (C["y"], C["x"]))
        print("  sudo apt install -y ffmpeg")
        return 0
    if a.dry:
        print("حالت آزمایشی، اجرا نشد.")
        return 0
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print("%sساخته شد:%s %s" % (C["g"], C["x"], out))
    else:
        print("%sخطا:%s %s" % (C["r"], C["x"], r.stderr[-500:]))
    return 0


# ───────────────────────────── status ─────────────────────────────

def cmd_status(a):
    proj = need_project()
    data = load(SHOTS, {"shots": []})
    led = load(LEDGER, {"entries": []})
    counts = {}
    total_dur = 0.0
    for s in data["shots"]:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
        if s["status"] == "approved":
            total_dur += float(s["duration"])
    print("\n%s%s%s" % (C["b"], proj["name"], C["x"]))
    print("مسیر تولید : %s" % proj["route"])
    print("مدل        : %s" % proj["model"])
    print("قالب       : %s  %s  %s fps" % (proj["aspect"], proj["resolution"], proj["fps"]))
    print("کاراکترها  : %s" % (", ".join(proj["characters"]) or "—"))
    print("\nپلان‌ها:")
    for k in ("planned", "generated", "approved", "rejected"):
        print("  %-10s %d" % (k, counts.get(k, 0)))
    print("\nمدت تأییدشده : %.0f ثانیه" % total_dur)
    print("کل تلاش‌ها    : %d" % len(led["entries"]))
    cost = sum(float(e.get("cost") or 0) for e in led["entries"])
    if cost:
        print("هزینه ثبت‌شده: %.2f" % cost)
    per = {}
    for e in led["entries"]:
        per[e["model"]] = per.get(e["model"], 0) + 1
    if per:
        print("\nتلاش به تفکیک مدل:")
        for m, n in sorted(per.items(), key=lambda x: -x[1]):
            print("  %-16s %d" % (m, n))
    print()
    return 0


# ───────────────────────────── main ─────────────────────────────

def main():
    p = argparse.ArgumentParser(prog="motion", description="بازوی عملیاتی فاکسی ۶")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("init", help="ساخت پروژه ویدیو")
    s.add_argument("name")
    s.add_argument("--aspect", default="16:9")
    s.add_argument("--resolution", default="1920x1080")
    s.add_argument("--fps", type=int, default=24)
    s.add_argument("--duration", default="4")
    s.add_argument("--route", default="model", choices=["model", "rig"])
    s.add_argument("--model"); s.add_argument("--style")
    s.add_argument("--force", action="store_true")
    s.set_defaults(f=cmd_init)

    s = sub.add_parser("char", help="مدیریت کاراکترها")
    s.add_argument("action", choices=["add", "list"])
    s.add_argument("id", nargs="?"); s.add_argument("--desc")
    s.add_argument("--sheet"); s.add_argument("--prompt-name")
    s.add_argument("--trait", action="append")
    s.set_defaults(f=cmd_char)

    s = sub.add_parser("shot", help="مدیریت پلان‌ها")
    s.add_argument("action", choices=["add", "list", "set"])
    s.add_argument("--id"); s.add_argument("--char"); s.add_argument("--purpose")
    s.add_argument("--motion"); s.add_argument("--camera"); s.add_argument("--light")
    s.add_argument("--duration"); s.add_argument("--audio")
    s.add_argument("--status", choices=["planned", "generated", "approved", "rejected"])
    s.add_argument("--file")
    s.set_defaults(f=cmd_shot)

    s = sub.add_parser("prompt", help="ساخت پرامپت استاندارد شش‌جزئی")
    s.add_argument("--id"); s.set_defaults(f=cmd_prompt)

    s = sub.add_parser("log", help="ثبت تلاش تولید")
    s.add_argument("shot"); s.add_argument("--model", required=True)
    s.add_argument("--result", required=True, choices=["generated", "approved", "rejected"])
    s.add_argument("--note"); s.add_argument("--cost", type=float)
    s.set_defaults(f=cmd_log)

    s = sub.add_parser("qa", help="بررسی عددی خروجی‌ها")
    s.add_argument("files", nargs="*"); s.add_argument("--width", type=int)
    s.add_argument("--height", type=int); s.add_argument("--frames", action="store_true")
    s.set_defaults(f=cmd_qa)

    s = sub.add_parser("assemble", help="چیدمان پلان‌های تأییدشده")
    s.add_argument("--out"); s.add_argument("--audio"); s.add_argument("--dry", action="store_true")
    s.set_defaults(f=cmd_assemble)

    s = sub.add_parser("status", help="وضعیت پروژه"); s.set_defaults(f=cmd_status)

    a = p.parse_args()
    if not getattr(a, "f", None):
        p.print_help(); return 0
    return a.f(a) or 0


if __name__ == "__main__":
    sys.exit(main())
