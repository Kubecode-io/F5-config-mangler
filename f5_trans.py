import sys
#fh = open('f5_utf16.txt', 'r', encoding='utf-16')
#fh = open('configs/analytics.txt', 'r')
#fh = open('configs/ltm_node.txt', 'r')
#fh = open('configs/ltm_policy.txt', 'r')
# fh = open('configs/ltm_virtual_address.txt', 'r')
# fh = open('configs/ltm_virtual.txt', 'r')
fh = open('configs/all.txt', 'r')
lines = fh.readlines()
fo = open('output/config.cfg', 'w')
bracket = 0
object_header = ""
object_body = ""
#for i in range(0,100):
#    print(lines[i])
#sys.exit()

for i,line in enumerate(lines):
    ignore_brackets = False
    line = line.rstrip(' ')
    #print("LINE:", line)
    #print("BRACKET:", bracket)
    if '{' in line and '}' in line:
        ignore_brackets = True
    if line.strip():
        if line.strip()[0]== '#':
           ignore_brackets = True
    # if len(line) < 2:
    #     ignore_brackets = True
    if not ignore_brackets:
        if '{' in line:
            bracket += 1
        if '}' in line:
            bracket -= 1
        # irules mess up bracket count
        if bracket < 0:
            bracket = 0
        # if bracket == 1 and line[-1] == "{":
        if bracket == 1 and 'ltm' in line:
            object_header = line
    # print("BRACKET:", bracket)
    # print("HEADER:", object_header)
    if object_header.startswith('ltm pool'):
        # Find/replace
        line = line.replace('/Common', '/NPA')
    elif object_header.startswith('ltm virtual-address'):
        # Find/replace
        line = line.replace('route-advertisement selective', 'route-advertisement disabled')
        line = line.replace('route-advertisement enabled', 'route-advertisement disabled')
    elif object_header.startswith('ltm virtual'):
        # Find/replace
        line = line.replace('ltm virtual /Common', 'ltm virtual /NPA')
        if bracket == 1:
            line = line.replace('pool /Common', 'pool /NPA')
        line = line.replace('destination /Common', 'destination /NPA')

    fo.write(line)
    #print("|--------------------------------|")
fh.close()
fo.close()
