import argparse
from pprint import pprint
import yaml

parser = argparse.ArgumentParser(description='Change partition for F5 virtual servers ')
parser.add_argument('-m', '--map', type=str, help='Map file in partition_map directory', required=True)
parser.add_argument('-i', '--input', type=str, help='Input F5 config file in configs directory', default='config.txt')
parser.add_argument('-o', '--output', type=str, help='Output file in output directory', default='config.txt')
args = parser.parse_args()

bracket = 0
object_header = ""
vs_dict = {}
pool_dict = {}
vs_address_dict = {}

with open(f'partition_map/{args.map}', 'r') as fp:
    partition_map = yaml.load(fp, Loader=yaml.SafeLoader)
fh = open(f'configs/{args.input}', 'r')
lines = fh.readlines()
print(f"Reading {len(lines)} lines from input file.")
for i,line in enumerate(lines):
    ignore_brackets = False
    line = line.rstrip(' ')
    if '{' in line and '}' in line:
        ignore_brackets = True
    if line.strip():
        if line.strip()[0]== '#':
           ignore_brackets = True
    if not ignore_brackets:
        if '{' in line:
            bracket += 1
        if '}' in line:
            bracket -= 1
        # irules mess up bracket count
        if bracket < 0:
            bracket = 0
        if bracket == 1 and 'ltm' in line:
            object_header = line
    # print("BRACKET:", bracket)
    # print("HEADER:", object_header)
    if object_header.startswith('ltm virtual'):
        virtual_name = object_header.split()[2]
        if virtual_name in vs_dict.keys():
            if 'destination' in line:
                vs_dict[virtual_name]['destination'] = line.split()[1].split(':')[0]
            if bracket == 1 and 'pool' in line:
                vs_dict[virtual_name]['pool'] = line.split()[1]
        else:
            vs_dict[virtual_name] = {}
            if virtual_name in partition_map.keys():
                vs_dict[virtual_name]["target_partition"] = partition_map[virtual_name]
            else:
                vs_dict[virtual_name]["target_partition"] = ""
# Build translation dictionaries
for vs, vs_data in vs_dict.items():
    if 'pool' in vs_data.keys():
        if vs_data['pool'] not in pool_dict.keys():
            pool = vs_data['pool']
            pool_dict[pool] = vs_data['target_partition']
    if 'destination' in vs_data.keys():
        if vs_data['destination'] not in vs_address_dict.keys():
            vs_address = vs_data['destination']
            vs_address_dict[vs_address] = vs_data['target_partition']

print(f"{len(vs_dict)} virtuals found.")
print(f"{len(pool_dict)} pools found.")
print(f"{len(vs_address_dict)} vs addresses found.")

# Reset pointer to start of input file
fh.seek(0)
lines = fh.readlines()
fo = open('output/config.cfg', 'w')
bracket = 0
object_header = ""
target_partition = ''
partition = ''
# Second pass of config file
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
    # pool objects
    if object_header.startswith('ltm pool'):
        # Find/replace
        if line.startswith('ltm pool'):
            fq_pool_name = line.split(' ')[2]
            if fq_pool_name in pool_dict.keys():
                target_partition = pool_dict[fq_pool_name]
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(partition, target_partition)
            else:
                target_partition = ''
                partition = ''
        # Member have ":" in name
        if ':' in line and target_partition and partition:
            line = line.replace(partition, target_partition)
    # virtual-address objects
    elif object_header.startswith('ltm virtual-address'):
        if line.startswith('ltm virtual-address'):
            fq_virtual_address = line.split(' ')[2]
            if fq_virtual_address in vs_address_dict.keys():
                target_partition = vs_address_dict[fq_virtual_address]
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(partition, target_partition)
            else:
                target_partition = ''
                partition = ''
        line = line.replace('route-advertisement selective', 'route-advertisement disabled')
        line = line.replace('route-advertisement enabled', 'route-advertisement disabled')
    # virtual objects
    elif object_header.startswith('ltm virtual'):
        if line.startswith('ltm virtual '):
            fq_virtual_server = line.split(' ')[2]
            if fq_virtual_server in vs_dict.keys():
                target_partition = vs_dict[fq_virtual_server]['target_partition']
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(partition, target_partition)
            else:
                target_partition = ''
                partition = ''
        elif 'destination' in line:
            line = line.replace(partition, target_partition)
        elif 'pool' in line and bracket == 1:
            line = line.replace(partition, target_partition)
    fo.write(line)
fh.close()
fo.close()