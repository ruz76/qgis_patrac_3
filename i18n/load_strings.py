with open('qgis_patrac_XX.ts') as xx:
    content = xx.read()
with open('qgis_patrac_ua_UA_strings.ts') as ts:
    lines = ts.readlines()
    pos = 0
    for line in lines:
        content = content.replace('__' + str(pos) + '__', line.rstrip())
        pos += 1
with open('qgis_patrac_ua_UA.ts', 'w') as ts:
    ts.write(content)
