#!/usr/bin/env python3
"""Достаёт CRC экспортируемых символов из собранного дерева и сверяет с эталоном.

В 5.10 CRC хранятся двумя способами (scripts/Makefile.build):
  * с CONFIG_LTO_CLANG -> текстовые файлы <obj>.o.symversions
  * без LTO            -> абсолютные символы __crc_<sym> внутри .o
Поддерживаем оба.
"""
import glob, json, os, re, subprocess, sys

subdir = sys.argv[1] if len(sys.argv) > 1 else 'net/wireless'
ref_path = sys.argv[2]

crcs = {}

# 1) .symversions (путь с LTO)
sv = glob.glob(f'{subdir}/*.symversions') + glob.glob(f'{subdir}/.*.symversions')
for f in sv:
    for line in open(f, errors='replace'):
        m = re.search(r'__crc_(\S+)\s*=\s*(0x[0-9a-fA-F]+)', line)
        if m:
            crcs[m.group(1)] = int(m.group(2), 16) & 0xffffffff

# 2) символы __crc_ в объектах (путь без LTO)
nm = os.environ.get('NM', 'llvm-nm')
objs = glob.glob(f'{subdir}/*.o')
nm_ok = 0
for o in objs:
    try:
        r = subprocess.run([nm, o], capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f'  nm не запустился на {o}: {e}', file=sys.stderr)
        continue
    if r.returncode == 0:
        nm_ok += 1
    for line in r.stdout.splitlines():
        p = line.split()
        if len(p) >= 3 and p[-1].startswith('__crc_'):
            try:
                crcs.setdefault(p[-1][6:], int(p[0], 16) & 0xffffffff)
            except ValueError:
                pass

print(f'диагностика: объектов={len(objs)}, nm отработал на {nm_ok}, '
      f'.symversions файлов={len(sv)}, всего собрано CRC={len(crcs)}')
if crcs and len(crcs) < 5:
    print('  примеры:', list(crcs.items())[:5])

ref = json.load(open(ref_path))
ok = bad = miss = 0
print()
print('%-34s %-12s %-12s' % ('СИМВОЛ', 'УСТРОЙСТВО', 'ЭТО ДЕРЕВО'))
for k, v in sorted(ref.items()):
    got = crcs.get(k)
    if got is None:
        print('%-34s 0x%08x   -- не найден --' % (k, v)); miss += 1
    elif got == v:
        print('%-34s 0x%08x   0x%08x  СОВПАЛ' % (k, v, got)); ok += 1
    else:
        print('%-34s 0x%08x   0x%08x  РАСХОЖДЕНИЕ' % (k, v, got)); bad += 1

print()
print('совпало=%d расхождений=%d не найдено=%d' % (ok, bad, miss))
if miss == len(ref):
    print('ВЕРДИКТ: ПРОБА НЕ СРАБОТАЛА (ни одного CRC не извлечено) — выводы делать нельзя')
elif bad == 0 and ok > 0:
    print('ВЕРДИКТ: ABI СОВМЕСТИМ')
else:
    print('ВЕРДИКТ: ABI НЕ СОВПАДАЕТ')
