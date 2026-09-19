# -*- coding: utf-8 -*-
"""imgverify.py — 图片闸门校验器（旅行路书用图）

起因：旧流程 __盲取小红书第 N 张图__ 直接入页面，没有内容识别 / 关键词一致性 /
素材类型判别 / 有效性筛查，导致「图与途经点不匹配」大量错误。
本脚本是那个缺口的正式填法。

> 设计前提：**图片是加分项，不是核心交付物。**
> 所以默认走**轻量档**（只跑 ①②），把"破图/畸形图"挡住即可；
> 只有用户明确要求"图必须对得上"时才用完整档。

三档路径
  light（默认）  ① 有效性 + ② 尺寸       —— 挡住破图与畸形图，成本极低
  full           ①~⑤ 全跑                —— 额外挡「素材类型」「语义不匹配」，需要 near 文案
  自定义          --gates 1245 等编号串

五道闸门
  ① 有效性      naturalWidth/字节数/HTTP 状态 —— 挡防盗链占位图
  ② 尺寸合理性  最短边 ≥ MIN_SIDE；宽高比在 [0.5, 2.0] —— 挡长图拼接/横条
  ③ 素材类型    排除头像/icon/emoji/攻略信息图（图上文字密度 + 邻近文案词表）
  ④ 语义一致性  邻近文案 + alt + 笔记标题 必须命中该 POI 的核心关键词
  ⑤ 落盘断言    cat 与文件名互锁：photos/d{天}-{cat}.webp

任一闸门不过 → 换下一候选；全部候选失败 → 记入 skip，不阻断交付。

用法：
    # 默认轻量档：只跑 ①②
    python imgverify.py --cand cands.json --out verdict.json

    # 完整档：五道全跑（需要候选带 near 文案）
    python imgverify.py --cand cands.json --gates full

    # 自选闸门
    python imgverify.py --cand cands.json --gates 1245

    # 校验已落盘的图片（②③ 只能做尺寸与文字密度）
    python imgverify.py --scan photos/ --json

候选 JSON 结构（由 bsk evaluate 产出，见 SKILL.md「取图」一节）：
[
  {"src":"https://...", "w":1080, "h":1440, "alt":"", "near":"某景点核心词的邻近文案…",
   "note_title":"某篇笔记标题", "bytes":0, "text_ratio":null, "is_avatar":false},
  ...
]
"""
import argparse
import io
import json
import os
import re
import sys
import traceback

# ── 闸门阈值（可被 --config 覆盖） ─────────────────────────────────────────
TH = {
    'min_side': 480,        # ② 最短边下限（px）
    'min_bytes': 20 * 1024,  # ① 文件字节下限，挡防盗链占位图
    'ratio_lo': 0.5,        # ② 宽高比下限（宽/高）
    'ratio_hi': 2.0,        # ② 宽高比上限
    'max_text_ratio': 0.35,  # ③ 图上文字覆盖比例上限（信息图/截图预警）
    # ③ 素材类型排除词（出现在邻近文案或 alt 里 → 判为攻略信息图/无关素材）
    'junk_words': ['攻略', '行程单', '清单', '价格表', '门票价格', '时间表', '路线图',
                   '地图', '导航截图', '表格', '汇总', '防坑', '指南', '避雷',
                   '关注我', '点赞', '收藏', '私信', '评论区', '同款', '链接'],
    # ③ 头像/图标类
    'avatar_words': ['头像', 'avatar', 'logo', 'icon', '二维码', 'qrcode', '水印'],
    # ④ 语义泛词（只命中这些不算通过 —— 太宽泛，任何图都命中）
    'stop_words': ['旅行', '旅游', '攻略', '拍照', '打卡', '风景', '美食', '推荐',
                   '一日游', '自驾', '路线', '分享', '记录', 'vlog', '日常'],
    # ④ 分类必含词族（cat=food 的图必须命中菜品/食物类词之一）
    'cat_hint': {
        'food': ['吃', '餐', '菜', '粉', '面', '汤', '肉', '饼', '饭', '酒', '茶',
                 '小吃', '火锅', '烧烤', '奶茶', '甜品', '早', '夜宵', '食'],
        'sight': ['景', '湖', '山', '寺', '窟', '塔', '城', '宫', '公园', '遗址',
                  '博物馆', '古镇', '峡谷', '丹霞', '雅丹', '日落', '日出', '夜'],
        'stay': ['酒店', '民宿', '客栈', '住宿', '房间', '床位'],
        'charge': ['充电', '充电桩', '超充', '补能', '换电'],
    },
}

RULE = '=' * 68


def norm(s):
    return re.sub(r'\s+', '', (s or '')).lower()


def load_photo_json(path):
    d = json.load(io.open(path, encoding='utf-8'))
    return {k: v for k, v in d.items() if not k.startswith('_')}


# ── 五道闸门 ───────────────────────────────────────────────────────────────

def gate1_valid(c, th):
    """① 有效性"""
    if c.get('is_avatar'):
        return False, '① 是头像元素'
    if c.get('w') is not None and int(c.get('w') or 0) <= 0:
        return False, '① naturalWidth=0（破图 / 未加载）'
    if c.get('h') is not None and int(c.get('h') or 0) <= 0:
        return False, '① naturalHeight=0'
    b = c.get('bytes')
    if b is not None and 0 < int(b) < th['min_bytes']:
        return False, '① 字节 %d < %d（疑似防盗链占位图）' % (int(b), th['min_bytes'])
    if c.get('http') and int(c['http']) >= 400:
        return False, '① HTTP %s' % c['http']
    return True, '① 有效'


def gate2_size(c, th):
    """② 尺寸合理性"""
    try:
        w, h = int(c['w']), int(c['h'])
    except Exception:
        return True, '② 尺寸未知，跳过'
    if min(w, h) < th['min_side']:
        return False, '② 最短边 %d < %d' % (min(w, h), th['min_side'])
    r = w / float(h)
    if not (th['ratio_lo'] <= r <= th['ratio_hi']):
        return False, '② 宽高比 %.2f 越界 [%.1f, %.1f]（长图拼接/横条）' % (
            r, th['ratio_lo'], th['ratio_hi'])
    return True, '② %dx%d (%.2f)' % (w, h, r)


def gate3_kind(c, th):
    """③ 素材类型判别"""
    hay = norm(c.get('near', '')) + ' ' + norm(c.get('alt', '')) + ' ' + norm(c.get('note_title', ''))
    for w in th['avatar_words']:
        if norm(w) in hay:
            return False, '③ 疑似头像/图标/水印（命中「%s」）' % w
    hits = [w for w in th['junk_words'] if norm(w) in norm(c.get('near', ''))]
    if len(hits) >= 2:
        return False, '③ 疑似攻略信息图/截图（邻近文案命中 %s）' % '/'.join(hits[:3])
    tr = c.get('text_ratio')
    if tr is not None and float(tr) > th['max_text_ratio']:
        return False, '③ 图上文字密度 %.2f > %.2f（疑似信息图）' % (float(tr), th['max_text_ratio'])
    return True, '③ 通过'


def gate4_semantic(c, th):
    """④ 语义一致性 —— 必须有 POI 核心词命中，且不能只命中泛词"""
    kws = [k for k in (c.get('keywords') or []) if k]
    if not kws:
        return True, '④ 未提供 keywords，跳过（⚠️ 建议补齐）'
    hay = norm(c.get('near', '')) + ' ' + norm(c.get('alt', '')) + ' ' + norm(c.get('note_title', ''))
    hit = [k for k in kws if norm(k) in hay]
    strong = [k for k in hit if norm(k) not in [norm(s) for s in th['stop_words']]]
    if not hit:
        return False, '④ 邻近文案未命中任何关键词 %s' % kws[:4]
    if not strong:
        return False, '④ 只命中泛词 %s，不足以判为对应图' % hit[:3]
    # 分类词族校验
    cat = c.get('cat')
    if cat in th['cat_hint']:
        fam = th['cat_hint'][cat]
        if not any(norm(f) in hay for f in fam):
            return False, '④ cat=%s 但文案无该类词族（%s）' % (cat, '/'.join(fam[:6]))
    return True, '④ 命中 %s' % '/'.join(strong[:3])


def gate5_naming(c, th):
    """⑤ 落盘命名断言：photos/d{天:02d}-{cat}.webp（天数为两位补零）"""
    day, cat = c.get('day'), c.get('cat')
    if not day or not cat:
        return True, '⑤ 未提供 day/cat，跳过'
    d = re.sub(r'^[Dd]', '', str(day)).strip()          # 去掉可能的 D 前缀
    if d.isdigit():
        d = '%02d' % int(d)                             # 统一补零到两位
    expect = 'photos/d%s-%s.webp' % (d, cat)
    img = c.get('img')
    if img and img != expect:
        return False, '⑤ 命名不符约定：%s ≠ %s' % (img, expect)
    return True, '⑤ %s' % expect


GATES = [('valid', gate1_valid), ('size', gate2_size), ('kind', gate3_kind),
         ('semantic', gate4_semantic), ('naming', gate5_naming)]

# ── 分级路径（见 SKILL.md Phase 5）────────────────────────────────────────
# 图片是加分项而非核心交付物，因此默认走轻量档：
#   轻量 = 只跑 ①②（有效性 + 尺寸）—— 挡住破图与畸形图，成本极低
#   完整 = 五道全跑 —— 额外挡「素材类型」「语义不匹配」，需要 near 文案，成本高
PATHS = {
    'light': ['valid', 'size'],                    # 默认
    'full': ['valid', 'size', 'kind', 'semantic', 'naming'],
}


def select_gates(spec):
    """spec 可为档位名（light/full）或闸门编号串（如 '12' / '1245' / '1,2,4,5'）"""
    if not spec:
        return GATES[:]
    s = str(spec).strip().lower()
    if s in PATHS:
        want = set(PATHS[s])
        return [(n, f) for n, f in GATES if n in want]
    # 数字串 → 闸门序号
    idx = [int(ch) for ch in re.findall(r'\d', s)]
    idx = [i for i in idx if 1 <= i <= len(GATES)]
    if not idx:
        return GATES[:]
    return [GATES[i - 1] for i in sorted(set(idx))]


def judge(cand, th, gates=None):
    """对一个候选跑指定闸门（默认全跑），返回 (pass, [逐步结果])"""
    steps, ok_all = [], True
    for name, fn in (gates or GATES):
        try:
            ok, msg = fn(cand, th)
        except Exception as e:
            ok, msg = False, '%s 异常: %s' % (name, str(e)[:60])
        steps.append({'gate': name, 'ok': ok, 'msg': msg})
        if not ok:
            ok_all = False
            break            # 第一道不过即淘汰，省算力
    return ok_all, steps


def pick(cands, th, gates=None):
    """按序尝试候选，返回第一个全通过的"""
    log = []
    for i, c in enumerate(cands):
        ok, steps = judge(c, th, gates)
        log.append({'idx': i, 'src': (c.get('src') or '')[:90], 'pass': ok,
                    'steps': steps, 'cand': c})
        if ok:
            return c, log, i
    return None, log, -1


# ── 已落盘图片的静态扫描（②③ 降级版） ─────────────────────────────────────

def scan_dir(d, th):
    """对已存在的图片目录做可做的检查：尺寸、宽高比、（可选）文字密度"""
    out = []
    try:
        from PIL import Image
    except Exception as e:
        return [{'file': '—', 'ok': False, 'msg': 'Pillow 未安装，无法扫描: %s' % e}]
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
            continue
        p = os.path.join(d, f)
        rec = {'file': f, 'ok': True, 'msg': ''}
        try:
            sz = os.path.getsize(p)
            im = Image.open(p)
            w, h = im.size
            r = w / float(h)
            msgs = []
            if sz < th['min_bytes']:
                rec['ok'] = False
                msgs.append('字节 %d < %d' % (sz, th['min_bytes']))
            if min(w, h) < th['min_side']:
                rec['ok'] = False
                msgs.append('最短边 %d < %d' % (min(w, h), th['min_side']))
            if not (th['ratio_lo'] <= r <= th['ratio_hi']):
                rec['ok'] = False
                msgs.append('宽高比 %.2f 越界' % r)
            # 命名约定
            if not re.match(r'^d\d{2}-(food|sight|stay|charge)(\d)?\.webp$', f):
                msgs.append('命名不符 d{天}-{类型}.webp 约定（当前 %s）' % f)
            rec['size'] = '%dx%d' % (w, h)
            rec['kb'] = round(sz / 1024, 1)
            rec['msg'] = '；'.join(msgs) or 'ok'
        except Exception as e:
            rec['ok'] = False
            rec['msg'] = '读取失败: %s' % str(e)[:60]
        out.append(rec)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cand', default='', help='候选 JSON 路径（bsk evaluate 产出）')
    ap.add_argument('--out', default='', help='判定报告写入路径')
    ap.add_argument('--scan', default='', help='改为扫描一个已存在的图片目录')
    ap.add_argument('--config', default='', help='阈值覆盖 JSON')
    ap.add_argument('--gates', default='light',
                    help='跑哪几道闸门：light（默认，仅①②）/ full（五道全跑）/ 编号串如 1245')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    th = dict(TH)
    if a.config and os.path.isfile(a.config):
        try:
            th.update(json.load(io.open(a.config, encoding='utf-8')))
        except Exception as e:
            print('配置读取失败，使用默认: %s' % e)

    gates = select_gates(a.gates)
    gnames = [n for n, _ in gates]

    rep = []
    def emit(s=''):
        rep.append(s)

    try:
        if a.scan:
            recs = scan_dir(a.scan, th)
            bad = [r for r in recs if not r['ok']]
            emit(RULE)
            emit('图片目录扫描: %s' % a.scan)
            emit(RULE)
            for r in recs:
                emit('  %s %-24s %-12s %8s KB  %s' % (
                    '✅' if r['ok'] else '❌', r['file'], r.get('size', ''),
                    r.get('kb', ''), r['msg']))
            emit()
            emit('合计 %d 张，问题 %d 张' % (len(recs), len(bad)))
            if a.json:
                print(json.dumps({'scan': recs, 'bad': len(bad)}, ensure_ascii=False, indent=2))
            else:
                print('\n'.join(rep))
            sys.exit(0)

        if not a.cand:
            ap.error('需要 --cand 或 --scan')

        cands = json.load(io.open(a.cand, encoding='utf-8'))
        if isinstance(cands, dict):
            cands = cands.get('candidates') or cands.get('cands') or []

        chosen, log, idx = pick(cands, th, gates)
        emit(RULE)
        emit('图片闸门判定  |  候选 %d 个  |  闸门: %s' % (len(cands), '＋'.join(gnames)))
        emit(RULE)
        for e in log:
            emit()
            emit('[%d] %s  %s' % (e['idx'] + 1, '✅ 通过' if e['pass'] else '❌ 淘汰',
                                  e['src']))
            for st in e['steps']:
                emit('      %s %s' % ('✅' if st['ok'] else '❌', st['msg']))
        emit()
        emit(RULE)
        if chosen:
            emit('采用第 %d 个候选' % (idx + 1))
            _d = re.sub(r'^[Dd]', '', str(chosen.get('day', ''))).strip()
            if _d.isdigit():
                _d = '%02d' % int(_d)
            emit('  落盘应为: %s' % ('photos/d%s-%s.webp' % (_d, chosen.get('cat', ''))))
        else:
            emit('❌ 全部候选未通过 —— 按降级策略处理：')
            emit('   1) 换更精确的关键词重搜（例：从「某地」换成「某地 具体地标/机位名」）')
            emit('   2) 仍无 → 该位不放图，记入 skip 报告（页面自然收窄，不破版）')
            emit('   3) 用户想补 → 按 图片替换/D{天}-{类型}-{名称}.png 丢文件后自动替换')
            if 'semantic' not in gnames:
                emit('   ⓘ 当前为轻量档，未跑语义闸门。若在意"图与途经点是否匹配"，')
                emit('     用 --gates full 重跑（需要候选带 near 文案）。')
        emit(RULE)

        if a.out:
            io.open(a.out, 'w', encoding='utf-8').write('\n'.join(rep))
            print('报告已写入: %s' % a.out)
        else:
            print('\n'.join(rep))
        sys.exit(0 if chosen else 1)

    except Exception:
        print('FATAL:\n' + traceback.format_exc())
        sys.exit(2)


if __name__ == '__main__':
    main()
