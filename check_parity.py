import json
plan = json.load(open('out/test_plan.json'))
tls = json.load(open('out/timelines.json'))
print(f"{'Test ID':<10} | {'Plan Reqs':<25} | {'Timeline Reqs':<25}")
print('-' * 65)
for p in plan:
    tid = p['test_id']
    tl = next((t for t in tls if t['test_id'] == tid), None)
    preqs = ','.join(p.get('requirement_ids', []))
    tlreqs = ','.join(tl.get('requirement_ids', [])) if tl else 'N/A'
    print(f"{tid:<10} | {preqs:<25} | {tlreqs:<25}")
