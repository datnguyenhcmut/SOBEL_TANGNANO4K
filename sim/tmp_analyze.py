import re
from collections import Counter
actual = {}
expected = {}
printed_sample = False
with open('sim_random.log', encoding='utf-16') as f:
    for line in f:
        if '[MISMATCH' not in line:
            continue
        if not printed_sample:
            print('sample line:', line.strip())
            printed_sample = True
        m = re.search(r'got=([0-9a-fA-F]+) exp=([0-9a-fA-F]+) \(idx=(\d+)', line)
        if not m:
            continue
        got = int(m.group(1), 16)
        exp = int(m.group(2), 16)
        idx = int(m.group(3))
        actual[idx] = got
        expected[idx] = exp
counter = Counter()
for idx in sorted(actual):
    got = actual[idx]
    exp = expected.get(idx)
    if exp is None:
        continue
    if got == exp:
        counter['equal'] += 1
    else:
        counter['notequal'] += 1
    prev = expected.get(idx-1)
    if prev is not None and got == prev:
        counter['matches_prev'] += 1
    prev2 = expected.get(idx-2)
    if prev2 is not None and got == prev2:
        counter['matches_prev2'] += 1
print('entries', len(actual))
print(counter)
