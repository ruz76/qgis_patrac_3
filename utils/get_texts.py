with open('/home/jencek/qgis3_profiles/profiles/default/python/plugins/qgis_patrac/main/report_export_cs.py') as s:
    lines = s.readlines()
    for line in lines:
        items = line.split("'")
        if len(items) > 1:
            print(items[1])
