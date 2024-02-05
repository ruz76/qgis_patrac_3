import sys, os
# Removes edges from graph that are in all graphs with smaller position number (previously created)
# params: path index_of_current_computation
# Example remove_duplicate_edges.py /path/to/working_directory 3

existing_edges = []
for i in range(int(sys.argv[2]) - 1):
    with open(os.path.join(sys.argv[1], str(i+1) + ".csv")) as gr:
        lines = gr.readlines()
        pos = 0
        for line in lines:
            # Skip the first line
            if pos > 0:
                items = line.split(',')
                existing_edges.append(items[3])
            pos += 1

print(existing_edges)

lines_to_export = []
with open(os.path.join(sys.argv[1], sys.argv[2] + ".csv")) as g1:
    lines = g1.readlines()
    for line in lines:
        items = line.split(',')
        if items[3] not in existing_edges:
            lines_to_export.append(line)

with open(os.path.join(sys.argv[1], sys.argv[2] + ".csv"), "w") as g1:
    for line in lines_to_export:
        g1.write(line)
