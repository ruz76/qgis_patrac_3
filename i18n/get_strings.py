def getContentStart(content):
    return content.find('<translation')
def getContentEnd(content):
    return content.find('</translation>')

with open('qgis_patrac_cs_CZ.ts') as ts:
    lines = ts.readlines()
    pos = 0
    with open('qgis_patrac_XX.ts', 'w') as xx:
        with open('qgis_patrac_cs_CZ_strings.ts', 'w') as ss:
            for line in lines:
                if 'translation' in line:
                    print(line.rstrip())
                    ll = 13
                    if 'obsolete' in line.rstrip():
                        ll = 29
                    print(ll)
                    start = getContentStart(line.rstrip()) + ll
                    end = getContentEnd(line.rstrip())
                    ss.write(line.rstrip()[start:end] + '\n')
                    xx.write('<translation>__' + str(pos) + '__</translation>')
                    pos += 1
                else:
                    xx.write(line)
