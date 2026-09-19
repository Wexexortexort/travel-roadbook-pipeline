# -*- coding: utf-8 -*-
"""imgcrop.py — 把候选图裁成 3:4 并落盘，附命名断言与人工替换通道。

与 imgverify.py 配套：verify 负责「选对图」，本脚本负责「落地」。
命名约定（与 photos.json 的 cat 互锁，杜绝「景点图存成 food 名」那类错位）：
    photos/d{天:02d}-{cat}.webp        cat ∈ food|sight|stay|charge
    同名多张 → d{天:02d}-{cat}2.webp

同时也承担「用户手选图」通道：扫描 图片替换/ 目录下的
    D{天}-{类型}-{名称}.png
自动解析成 (day, cat, name) 三元组并替换，替代旧 replace_photos.py 里硬编码的 MAP。

用法：
    # 从本地文件裁切落盘
    python imgcrop.py --src raw/d09.jpg --day 9 --cat sight
    python imgcrop.py --batch raw/ --json raw/manifest.json

    # 用户手选图替换（自动解析文件名）
    python imgcrop.py --replace "E:/path/图片替换" --photos photos/ --backup backup/photos

    # 校验已落盘图片命名与尺寸
    python imgcrop.py --check photos/
"""
import argparse
import io
import json
import os
import re
import shutil
import sys
import traceback

TARGET_W, TARGET_H = 480, 640
QUALITY = 78
CAT_CN = {'美食': 'food', '景点': 'sight', '住宿': 'stay', '补给': 'charge',
          'food': 'food', 'sight': 'sight', 'stay': 'stay', 'charge': 'charge'}
VALUE_RE = re.compile(r'^D(\d{1,2})[-_—]?(.+?)[-_—]?(.+?)?\.(png|jpg|jpeg|webp)$', re.I)

RULE = '=' * 68


def crop34(im):
    """中心裁成 3:4；竖图略偏上保主体"""
    w, h = im.size
    if w / h > 3 / 4:
        nw = int(h * 3 / 4)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w * 4 / 3)
        top = max(0, (h - nh) // 3)
        im = im.crop((0, top, w, top + nh))
    return im


def save34(src, dst):
    from PIL import Image
    im = Image.open(src)
    if im.mode not in ('RGB',):
        im = im.convert('RGB')
    im = crop34(im).resize((TARGET_W, TARGET_H), Image.LANCZOS)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.save(dst, 'WEBP', quality=QUALITY, method=4)
    return os.path.getsize(dst)


def target_name(day, cat, photos_dir, force_idx=None):
    """命名与占据检查：同名已存在则递增序号"""
    d = 'd%02d' % int(str(day).lstrip('Dd'))
    if force_idx is None:
        base = os.path.join(photos_dir, '%s-%s.webp' % (d, cat))
        if not os.path.exists(base):
            return base
        i = 2
        while os.path.exists(os.path.join(photos_dir, '%s-%s%d.webp' % (d, cat, i))):
            i += 1
        return os.path.join(photos_dir, '%s-%s%d.webp' % (d, cat, i))
    return os.path.join(photos_dir, '%s-%s%s.webp' % (d, cat, force_idx))


def parse_replace_name(fn):
    """D10-景点-某地标.png -> ('10','sight','某地标')；解析不出返回 None"""
    m = VALUE_RE.match(fn)
    if not m:
        return None
    day = m.group(1)
    parts = [p for p in fn[:fn.rfind('.')].split('-')[1:] if p]
    if not parts:
        return None
    cat_raw = parts[0]
    cat = CAT_CN.get(cat_raw)
    if not cat:
        # 尝试在剩余部分里找类型词
        for p in parts:
            if p in CAT_CN:
                cat = CAT_CN[p]
                break
    if not cat:
        return None
    name = '-'.join(parts[1:]) if len(parts) > 1 else ''
    return day, cat, name


def do_replace(src_dir, photos_dir, backup_dir):
    """用户手选图替换通道（替代旧 replace_photos.py 的硬编码 MAP）"""
    rep, ok, fail = [], 0, 0
    os.makedirs(backup_dir, exist_ok=True)
    imgs = [f for f in sorted(os.listdir(src_dir))
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    rep.append(RULE)
    rep.append('用户手选图替换  |  源 %s  |  %d 个文件' % (src_dir, len(imgs)))
    rep.append(RULE)
    # 建立 photos/ 现有索引：day+cat -> 文件
    idx = {}
    for f in os.listdir(photos_dir) if os.path.isdir(photos_dir) else []:
        m = re.match(r'^d(\d{2})-(food|sight|stay|charge)(\d?)\.webp$', f)
        if m:
            idx.setdefault((m.group(1), m.group(2)), []).append(f)
    for fn in imgs:
        try:
            parsed = parse_replace_name(fn)
            if not parsed:
                rep.append('  跳过（文件名不可解析）: %s' % fn)
                continue
            day, cat, name = parsed
            cands = sorted(idx.get((day.zfill(2), cat), []))
            if not cands:
                rep.append('  ⚠️ 无对应目标位，追加为新图: %s -> d%s-%s' % (fn, day.zfill(2), cat))
                dst = target_name(day, cat, photos_dir)
            else:
                dst = os.path.join(photos_dir, cands[0])
            if os.path.isfile(dst):
                shutil.copy2(dst, os.path.join(backup_dir, os.path.basename(dst)))
            sz = save34(os.path.join(src_dir, fn), dst)
            ok += 1
            rep.append('  ✅ %-30s -> %-20s %6.1f KB' % (fn, os.path.basename(dst), sz / 1024))
        except Exception as e:
            fail += 1
            rep.append('  ❌ %s :: %s' % (fn, str(e)[:90]))
    rep.append('')
    rep.append('成功 %d ｜ 失败 %d ｜ 备份 %s' % (ok, fail, backup_dir))
    rep.append(RULE)
    rep.append('⚠️ 替换后必须重跑 build_photos_html / 页面重建，让 photos.json 的 img 路径同步')
    return '\n'.join(rep)


def do_check(photos_dir):
    """校验已落盘图片：命名约定 + 尺寸"""
    rep = [RULE, '命名与尺寸校验: %s' % photos_dir, RULE]
    bad = 0
    try:
        from PIL import Image
    except Exception as e:
        return 'Pillow 未安装: %s' % e
    for f in sorted(os.listdir(photos_dir)):
        if not f.lower().endswith('.webp'):
            continue
        okname = bool(re.match(r'^d\d{2}-(food|sight|stay|charge)\d?\.webp$', f))
        try:
            im = Image.open(os.path.join(photos_dir, f))
            w, h = im.size
            oksz = (w, h) == (TARGET_W, TARGET_H)
        except Exception as e:
            w = h = 0
            oksz = False
        if not (okname and oksz):
            bad += 1
        rep.append('  %s %-24s %dx%d %s' % (
            '✅' if (okname and oksz) else '⚠️', f, w, h,
            '' if okname else '← 命名不符约定'))
    rep.append('')
    rep.append('问题 %d 个' % bad)
    return '\n'.join(rep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='')
    ap.add_argument('--day', default='')
    ap.add_argument('--cat', default='', choices=['food', 'sight', 'stay', 'charge'])
    ap.add_argument('--photos', default='photos')
    ap.add_argument('--idx', default=None, help='强制序号（同天同类多张：2、3…）')
    ap.add_argument('--batch', default='', help='批量目录 + --json 描述清单')
    ap.add_argument('--json', default='')
    ap.add_argument('--replace', default='', help='用户手选图目录，走自动解析替换')
    ap.add_argument('--backup', default='backup/photos')
    ap.add_argument('--check', default='', help='校验目录')
    a = ap.parse_args()

    rep = []
    try:
        if a.check:
            print(do_check(a.check))
            return

        if a.replace:
            out = do_replace(a.replace, a.photos, a.backup)
            print(out)
            io.open(os.path.join(os.path.dirname(a.photos.rstrip('/\\')) or '.',
                                 'replace-photos-report.txt'), 'w', encoding='utf-8').write(out)
            return

        if a.batch and a.json:
            items = json.load(io.open(a.json, encoding='utf-8'))
            rep.append(RULE)
            rep.append('批量裁切 -> %s' % a.photos)
            rep.append(RULE)
            ok = fail = 0
            for it in items:
                try:
                    src = os.path.join(a.batch, it['file']) if not os.path.isabs(it['file']) else it['file']
                    dst = target_name(it['day'], it['cat'], a.photos, it.get('idx'))
                    sz = save34(src, dst)
                    it['img'] = os.path.relpath(dst, os.path.dirname(a.photos.rstrip('/\\'))).replace('\\', '/')
                    ok += 1
                    rep.append('  ✅ %-28s -> %-22s %6.1f KB' % (it['file'], os.path.basename(dst), sz / 1024))
                except Exception as e:
                    fail += 1
                    rep.append('  ❌ %s :: %s' % (it.get('file'), str(e)[:90]))
            rep.append('')
            rep.append('成功 %d ｜ 失败 %d' % (ok, fail))
            print('\n'.join(rep))
            io.open(a.json, 'w', encoding='utf-8').write(json.dumps(items, ensure_ascii=False, indent=2))
            return

        if not (a.src and a.day and a.cat):
            ap.error('需要 --src + --day + --cat，或 --batch + --json，或 --replace，或 --check')
        dst = target_name(a.day, a.cat, a.photos, a.idx)
        sz = save34(a.src, dst)
        print('%s -> %s  %.1f KB' % (a.src, dst, sz / 1024))
        print('  命名符合约定: %s' % os.path.basename(dst))
    except Exception:
        print('FATAL:\n' + traceback.format_exc())
        sys.exit(2)


if __name__ == '__main__':
    main()
