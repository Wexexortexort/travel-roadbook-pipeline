# -*- coding: utf-8 -*-
"""preflight.py — travel-roadbook-pipeline 的前置依赖体检。

任何 agent 在开始做路书之前必须先跑这个脚本。它会逐项检测外部依赖是否就位，
输出「可用 / 缺失」两级结论，并对缺失项给出**可执行的安装或获取指引**。

> 产物是**本地单文件 HTML**，不需要 GitHub / 域名 / 服务器 / 任何部署凭据，
> 所以本脚本不检查任何发布相关依赖。

设计原则：
  * 只读检测，绝不自动安装任何东西（装不装由用户决定）
  * 容错模式：任何一项异常都不中断，逐项 try，最后汇总
  * 结果同时写文件（stdout 在本环境可能被吞）

用法：
    python preflight.py                 # 完整体检
    python preflight.py --json          # 机器可读
    python preflight.py --quick         # 只查关键项（amap + bsk）
    python preflight.py --workdir <dir> # 指定路书工作目录，额外检查产物结构
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback

# ── 依赖的可执行文件 / 密钥查找位置 ──────────────────────────────────────
# 设计为**路径无关**：先看环境变量覆盖，再查标准位置，最后退回 PATH。
# 若你的 bsk / Key 在别处，最省事的做法是设环境变量，不必改本文件：
#     BSK_PATH=<你的 bsk 可执行文件>
#     AMAP_KEY_FILE=<你的 amap.key 路径>
HOME = os.path.expanduser('~')


def _redact_path(p):
    """把绝对路径脱敏成可读形式：保留尾层与盘符/家目录语义，抹掉用户名。

    目的：输出可以放心贴进 issue 或截图，不带上本机用户名与目录结构。
    例：
      C:\\Users\\alice\\bin\\bsk.exe   → <home>\\bin\\bsk.exe
      /home/alice/.local/bin/bsk      → <home>/.local/bin/bsk
      E:\\work\\proj\\photos           → E:\\…\\photos
    """
    if not p:
        return p
    s = str(p)
    # 家目录整体替换（Windows 与 Unix 两种形态）
    for h in {HOME, HOME.replace('\\', '/'), HOME.replace('/', '\\')}:
        if h and s.lower().startswith(h.lower()):
            return '<home>' + s[len(h):]
    # 仍带盘符的绝对路径：保留盘符 + 尾两层
    m = re.match(r'^([A-Za-z]:)[\\/](.*)$', s)
    if m:
        rest = m.group(2).replace('/', '\\').strip('\\')
        parts = [x for x in rest.split('\\') if x]
        tail = '\\'.join(parts[-2:]) if parts else ''
        return '%s\\…\\%s' % (m.group(1), tail) if tail else '%s\\…' % m.group(1)
    # Unix 绝对路径：保留尾两层
    if s.startswith('/'):
        parts = [x for x in s.split('/') if x]
        return '/…/' + '/'.join(parts[-2:]) if parts else '/…'
    return s


# 输出前兜底扫描：这些串不该出现在任何会被分享的报告里
# 注意"吃干净"原则：命中一个键值对后要把整个值吃完，别留下尾巴（如 Bearer 后面的 JWT）
_SECRET_PAT = [
    ('xsec_token', re.compile(r'xsec_token=[^&\s"\']+')),
    ('xsec_source', re.compile(r'xsec_source=[^&\s"\']+')),
    ('cookie', re.compile(r'(?i)\bcookie\s*[:=]\s*[^\r\n]+')),
    ('authorization', re.compile(r'(?i)\bauthorization\s*[:=]\s*[^\r\n]+')),
    ('bearer', re.compile(r'(?i)\bbearer\s+[A-Za-z0-9._\-]+')),
    ('api_key', re.compile(r'(?i)\bapi[_-]?key\s*[:=]\s*\S+')),
    ('secret', re.compile(r'(?i)\bsecret\s*[:=]\s*\S+')),
    ('win_user_path', re.compile(r'(?i)[A-Z]:\\Users\\[^\\\s"\']+')),
    ('unix_user_path', re.compile(r'/(?:home|Users)/[^/\s"\']+')),
]


def _scan_secrets(text):
    """返回 [(名称, 命中的原文串)] —— 供输出前最后一道脱敏。"""
    found = []
    for name, pat in _SECRET_PAT:
        for m in pat.finditer(text):
            found.append((name, m.group(0)))
    # 同一串只报一次
    seen, out = set(), []
    for n, s in found:
        if s not in seen:
            seen.add(s)
            out.append((n, s))
    return out


def _cands(env_var, xdg_subs, extra=None):
    """按 环境变量 → ~/.workbuddy/keys → ~/.local/bin → PATH 的顺序给出候选。"""
    out = []
    v = os.environ.get(env_var)
    if v:
        out.append(v)
    if extra:
        out.extend(extra)
    for sub in xdg_subs:
        out.append(os.path.join(HOME, *sub))
    return out


KNOWN = {
    'bsk': _cands('BSK_PATH', [('.local', 'bin', 'bsk'), ('.local', 'bin', 'bsk.exe')]),
    'amap_key': _cands('AMAP_KEY_FILE', [('.workbuddy', 'keys', 'amap.key'),
                                         ('.config', 'amap', 'amap.key')]),
    'python': [sys.executable],
}

# 依赖清单：key -> (显示名, 必需性, 用途)
DEPS = {
    'python':  ('Python 3.10+',        'required', '运行全部构建与校验脚本'),
    'pillow':  ('Pillow (PIL)',        'required', '图片裁剪 3:4 / 压 WebP'),
    'fonttools': ('fontTools',         'optional', '中文衬线字体子集化（不用自托管字体则免）'),
    'requests': ('requests',           'optional', '部分下载通道更稳（可被 urllib 替代）'),
    'bsk':     ('browser-skill (bsk)', 'required', '小红书情报检索 + 图片抓取'),
    'bsk_ext': ('bsk 浏览器扩展在线',   'required', 'bsk 必须连到已登录的 Chrome'),
    'amap_key': ('高德 REST Key',      'required', '里程/时长/收费权威口径'),
}

RULE = '=' * 68


def first_exist(paths):
    for p in paths:
        if p and os.path.isfile(p):
            return p
    return None


def which(name):
    p = shutil.which(name)
    if p:
        return p
    # Windows 下找 .exe
    for ext in ('.exe', '.cmd', '.bat'):
        p = shutil.which(name + ext)
        if p:
            return p
    return None


def run(cmd, timeout=60, env=None):
    """执行子进程；失败返回 (False, 错误文本)"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                           errors='ignore', timeout=timeout, env=env)
        return (r.returncode == 0), ((r.stdout or '') + (r.stderr or ''))
    except Exception as e:
        return False, '%s' % e


def parse_bsk_status(out):
    """从 bsk status --json 里取 daemon 与浏览器数量；容忍非 JSON 输出"""
    try:
        d = json.loads(out[out.find('{'):out.rfind('}') + 1])
    except Exception:
        # 退化到正则（老版本 / 纯文本）
        n_browser = None
        m = re.search(r'browsers connected\s+(\d+)', out)
        if m:
            n_browser = int(m.group(1))
        m = re.search(r'active sessions\s+(\d+)', out)
        return n_browser, (int(m.group(1)) if m else None), out.strip()[:200]
    br = d.get('browsers')
    n_browser = len(br) if isinstance(br, list) else (br if isinstance(br, int) else None)
    return n_browser, d.get('active_sessions'), d.get('daemon_version') or d.get('version')


def check_python():
    v = sys.version_info
    ok = v >= (3, 10)
    return dict(ok=ok, detail='%d.%d.%d' % (v[0], v[1], v[2]),
                fix='' if ok else 'WorkBuddy 已自带 3.12/3.13/3.14，直接用管理版 Python 的绝对路径即可')


def check_module(name, import_name=None):
    import_name = import_name or name
    try:
        mod = __import__(import_name)
        v = getattr(mod, '__version__', '')
        return dict(ok=True, detail=('%s' % v) if v else '已安装', path=getattr(mod, '__file__', ''))
    except Exception as e:
        return dict(ok=False, detail=str(e)[:80],
                    fix='"%s" -m pip install %s' % (sys.executable, name))


def check_bsk(verbose=False):
    exe = first_exist(KNOWN['bsk']) or which('bsk')
    if not exe:
        return dict(ok=False, exe=None, detail='未找到 bsk 可执行文件',
                    fix=('安装 browser-skill：\n'
                         '    npm i -g browser-skill   # 或按其仓库说明安装\n'
                         '    安装后在 Chrome 里装 BrowserSkill 扩展并登录小红书\n'
                         '    文档：https://github.com/anthropics/browser-skill（以官方为准）'))
    env = dict(os.environ)
    env['PATH'] = os.path.dirname(exe) + os.pathsep + env.get('PATH', '')
    env['BSK_AUTO_START'] = '0'          # 避免重复拉起 daemon
    ok, out = run([exe, 'status', '--json'], timeout=45, env=env)
    # 默认只留可枚举的脱敏状态；bsk 原始输出可能含 URL / 账号标识 / 调试字段，
    # 只在 --verbose 时输出（且已做脱敏），避免它被顺手贴进 issue。
    raw = _redact_path(out.strip()[:200]) if verbose else None
    if not ok:
        d = dict(ok=True, exe=_redact_path(exe),
                 detail='bsk 存在，但 status 调用失败（daemon 可能未运行）',
                 browsers=None, daemon_online=False,
                 fix=('启动 daemon：\n    "%s" daemon start\n'
                      '若报权限/超时，daemon 可能其实在跑，直接重试 status'
                      % _redact_path(exe)))
        if raw:
            d['raw'] = raw
        return d
    nb, ns, ver = parse_bsk_status(out)
    if not nb:
        d = dict(ok=True, exe=_redact_path(exe),
                 detail='daemon 在线（%s），但没有连接浏览器' % (ver or '?'),
                 browsers=0, daemon_online=True,
                 fix=('bsk 需要连到你**已登录小红书**的 Chrome：\n'
                      '    1) 在 Chrome 里确认 BrowserSkill 扩展已启用\n'
                      '    2) 扩展里点击连接 / 或重启 Chrome\n'
                      '    3) 确认已登录 xiaohongshu.com（打开首页看看头像在不在）\n'
                      '    然后重跑：bsk status'))
        if raw:
            d['raw'] = raw
        return d
    d = dict(ok=True, exe=_redact_path(exe),
             detail='daemon %s，浏览器 %d 个已连接' % (ver or '?', nb),
             browsers=nb, sessions=ns, daemon_online=True, fix='')
    if raw:
        d['raw'] = raw
    return d


def check_keyfile(kind, label, verbose=False):
    p = first_exist(KNOWN[kind])
    if not p:
        fix = ('获取免费高德 Key：\n'
               '    1) https://lbs.amap.com 注册 + 实名认证（个人开发者即可）\n'
               '    2) 控制台 → 应用管理 → 创建应用 → 添加 Key\n'
               '    3) 🔴 服务平台必须选「Web 服务」（选成 JS API 会返回 INVALID_USER_KEY）\n'
               '    4) 存成文件，例：mkdir -p ~/.workbuddy/keys && echo "<你的KEY>" > ~/.workbuddy/keys/amap.key\n'
               '    ⚠️ 不要贴进对话 —— 对话通道会截断/脱敏疑似密钥（实测 40 字符只收到 24）')
        return dict(ok=False, path=None, detail='未找到 %s 文件' % label, fix=fix)
    try:
        val = io.open(p, encoding='utf-8', errors='ignore').read().strip()
    except Exception as e:
        return dict(ok=False, path=_redact_path(p), detail='读取失败: %s' % e,
                    fix='检查文件权限与编码')
    # 只报长度，绝不回显密钥本体、前缀、后缀或哈希。
    # 长度是必要的诊断信号（能区分"文件空的"和"Key 被对话通道截断了"），
    # 而它不泄露任何可用于猜测密钥的信息。
    n = len(val)
    shown = _redact_path(p) if verbose else '已找到'
    if n < 16:
        return dict(ok=False, path=shown, detail='文件存在但内容过短（%d 字符）' % n,
                    fix='疑似被截断。重新写入完整 Key（高德 Key 通常 32 位）')
    return dict(ok=True, path=shown, detail='已配置（长度 %d）' % n, fix='')


def check_workdir(wd):
    """检查路书工作目录的结构约定"""
    out = {}
    if not wd:
        return out
    out['exists'] = os.path.isdir(wd)
    if not out['exists']:
        out['fix'] = '目录不存在，首次运行需创建（参考 SKILL.md 的目录结构约定）'
        return out
    for name, desc in [('photos', '图片目录'), ('fonts', '字体子集目录'),
                       ('.build', '构建脚本目录')]:
        p = os.path.join(wd, name)
        out[name] = os.path.isdir(p)
    htmls = [f for f in os.listdir(wd) if f.endswith('.html')]
    out['html'] = htmls
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--quick', action='store_true', help='只查关键项：高德 Key + bsk')
    ap.add_argument('--workdir', default='', help='路书工作目录（可选）')
    ap.add_argument('--report', default='', help='报告写入路径（默认仅 stdout）')
    ap.add_argument('--verbose', action='store_true',
                    help='输出诊断细节（依赖路径、bsk 原始状态）。默认关闭：'
                         '输出已脱敏，便于直接贴进 issue 或截图')
    a = ap.parse_args()

    R = {'checks': {}, 'summary': {}}
    lines = []

    def emit(s=''):
        lines.append(s)

    try:
        if not a.quick:
            R['checks']['python'] = check_python()
            R['checks']['pillow'] = check_module('pillow', 'PIL')
            R['checks']['fonttools'] = check_module('fonttools', 'fontTools')
            R['checks']['requests'] = check_module('requests')
        R['checks']['bsk'] = check_bsk(verbose=a.verbose)
        R['checks']['amap_key'] = check_keyfile('amap_key', '高德 Key', verbose=a.verbose)
        if a.workdir:
            R['checks']['workdir'] = check_workdir(a.workdir)

        # ── 汇总 ──
        blocking, advisory = [], []
        for k, v in R['checks'].items():
            if k == 'workdir':
                continue
            ok = v.get('ok', False)
            level = DEPS.get(k, ('?', 'optional', ''))[1]
            if not ok:
                (blocking if level == 'required' else advisory).append(k)
            if k == 'bsk':
                # bsk 存在但浏览器没连上 → 也计入阻塞
                if v.get('ok') and v.get('browsers') == 0:
                    if 'bsk' not in blocking:
                        blocking.append('bsk_ext')

        R['summary'] = {
            'blocking': blocking,
            'advisory': advisory,
            'ready': not blocking,
        }

        # ── 人类可读输出 ──
        emit(RULE)
        emit('travel-roadbook-pipeline · 前置依赖体检')
        emit(RULE)
        emit()
        if not a.quick:
            emit('【运行环境】')
            for k in ('python', 'pillow', 'fonttools', 'requests'):
                v = R['checks'].get(k, {})
                mark = '✅' if v.get('ok') else '❌'
                emit('  %s %-22s %s' % (mark, DEPS[k][0], v.get('detail', '')))
            emit()
        emit('【外部工具】')
        for k in ('bsk', 'amap_key'):
            v = R['checks'].get(k, {})
            mark = '✅' if v.get('ok') else '❌'
            emit('  %s %-22s %s' % (mark, DEPS[k][0], v.get('detail', '')))
        wd = R['checks'].get('workdir')
        if wd:
            emit()
            emit('【工作目录】')
            emit('  存在: %s' % wd.get('exists'))
            for k in ('photos', 'fonts', '.build'):
                if k in wd:
                    emit('  %-12s %s' % (k, '✅' if wd[k] else '—'))
            if wd.get('html'):
                emit('  HTML 产物: %s' % ', '.join(wd['html']))

        # ── 缺失项与修复指引 ──
        fixes = [(k, R['checks'][k]) for k in (blocking + advisory)
                 if k in R['checks'] and (R['checks'][k].get('fix') or R['checks'][k].get('detail'))]
        if fixes:
            emit()
            emit(RULE)
            emit('❗ 需要处理的项（%d 个阻塞 / %d 个可选）' % (len(blocking), len(advisory)))
            emit(RULE)
            for i, (k, v) in enumerate(fixes, 1):
                tag = '阻塞' if k in blocking else '可选'
                emit()
                emit('[%d/%d] %s · %s' % (i, len(fixes), DEPS.get(k, (k,))[0], tag))
                if v.get('detail'):
                    emit('  现状: %s' % v['detail'])
                for ln in (v.get('fix') or '').splitlines():
                    emit('  ' + ln)

        emit()
        emit(RULE)
        if R['summary']['ready']:
            emit('✅ 全部关键依赖就位，可以开始规划')
        else:
            emit('❌ 缺少关键依赖，无法开始：%s' % ', '.join(blocking))
            emit('   请按上面的指引补齐后重新运行 preflight.py')
        emit(RULE)

    except Exception:
        emit('FATAL:\n' + traceback.format_exc())
        R['summary']['ready'] = False
        R['summary']['fatal'] = True

    text = '\n'.join(lines)

    # ── 输出前最后一道闸：确保报告里没有敏感串 ──
    # 这份输出经常会被贴进 issue 或截图分享，所以不能只依赖上面的逐点脱敏。
    leak = _scan_secrets(text)
    if leak:
        for name, sample in leak:
            text = text.replace(sample, '<redacted:%s>' % name)
        emit_guard = '[preflight] 已自动脱敏 %d 处敏感串（%s）' % (
            len(leak), ', '.join(sorted({n for n, _ in leak})))
        sys.stderr.write(emit_guard + '\n')

    if a.json:
        print(json.dumps(R, ensure_ascii=False, indent=2))
    else:
        print(text)

    if a.report:
        try:
            io.open(a.report, 'w', encoding='utf-8').write(text)
            print('\n报告已写入: %s' % _redact_path(a.report))
        except Exception as e:
            print('报告写入失败: %s' % e)

    sys.exit(0 if R['summary'].get('ready') else 1)


if __name__ == '__main__':
    main()
