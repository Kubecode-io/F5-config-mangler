import argparse
from pprint import pprint
import yaml

parser = argparse.ArgumentParser(description='Change partition for F5 virtual servers ')
parser.add_argument('-m', '--map', type=str, help='Map file in partition_map directory', required=True)
parser.add_argument('-i', '--input', type=str, help='Input F5 config file in configs directory', default='config.txt')
parser.add_argument('-o', '--output', type=str, help='Output file in output directory', default='config.txt')
parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
args = parser.parse_args()

bracket = 0
object_header = ""
object_subsection = ""
vs_dict = {}
pool_dict = {}
vs_address_dict = {}
rule_dict = {}

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
    # print("LINE:", line)
    if object_header.startswith('ltm rule'):
        rule_name = object_header.split()[2]
        if 'ltm rule ' in line:
            rule_dict.setdefault(rule_name, {})
            rule_dict[rule_name].setdefault("target_partition", "")
            rule_dict[rule_name].setdefault("pools", [])
        if 'set destpool' in line:
            pool = line.split('destpool')[1].replace('}', '').strip()
            if pool not in rule_dict[rule_name]["pools"]:
                rule_dict[rule_name]["pools"].append(pool)

    if object_header.startswith('ltm virtual '):
        virtual_name = object_header.split()[2]
        if virtual_name in vs_dict.keys():
            if 'destination' in line:
                vs_dict[virtual_name]['destination'] = line.split()[1].split(':')[0]
            if bracket == 1 and 'pool' in line:
                vs_dict[virtual_name]['pool'] = line.split()[1]
            if 'rules' in line and bracket == 2:
                object_subsection = 'RULE'
                rules_list = []
            elif object_subsection == 'RULE' and bracket > 1:
                rule = line.strip()
                rules_list.append(rule)
            elif object_subsection == 'RULE' and bracket == 1:
                object_subsection = ''
                vs_dict[virtual_name]['rules'] = rules_list
                rules_list = []

        else:
            vs_dict[virtual_name] = {}
            if virtual_name in partition_map.keys():
                vs_dict[virtual_name]["target_partition"] = partition_map[virtual_name]
            else:
                vs_dict[virtual_name]["target_partition"] = ""
# Build translation dictionaries
#
# Example 1. Pool explicit in ltm virtual
# VS_DICT
# {'/Common/BLUE-DGA-INT-NAP-V-1C-CSG_443_VS': {'destination': '/Common/10.130.13.163',
#                                               'pool': '/Common/BLUE-DGA-INT-NAP-V-1C-CSG_4443_POOL',
#                                               'target_partition': 'TEST'}}
# RULE_DICT:
# {}
# VS_ADDRESS_DICT:
# {'/Common/10.130.13.163': 'TEST'}
# POOL_DICT:
# {'/Common/BLUE-DGA-INT-NAP-V-1C-CSG_4443_POOL': 'TEST'}
#
# Eample 2. Pool derived from rule
#
# VS_DICT
# {'/WPG/BLUE-DGA-EXT-WPG_FUTUREPAY-TEST.WP.PTE3.TEST.WORLDPAY.COM_443_VS': {'destination': '/WPG/10.130.13.36',
#                                                                            'rules': ['/WPG/BLUE-DGA-EXT-WPG_PTE3_SECTION_FUTUREPAYTEST_RULE',
#                                                                                      '/WPG/BLUE-DGA-EXT-WPG_PTE3_SPLUNK_LOGGIN_RULE',
#                                                                                      '/WPG/BLUE-DGA-EXT-WPG_XFF_SERVER_SELECT_RULE',
#                                                                                      '/WPG/BLUE-DGA-EXT-WPG_SSL_VERSION_HEADER_INSERT_RULE'],
#                                                                            'target_partition': 'TEST-WPG'}}
# RULE_DICT:
# {'/WPG/BLUE-DGA-EXT-WPG_PTE3_SECTION_FUTUREPAYTEST_RULE': {'pools': ['/WPG/BLUE-DGA-EXT-WPG_PTE3_SECURETEST_POOL'],
#                                                            'target_partition': 'TEST-WPG'},
#  '/WPG/BLUE-DGA-EXT-WPG_PTE3_SPLUNK_LOGGIN_RULE': {'pools': [],
#                                                    'target_partition': 'TEST-WPG'},
#  '/WPG/BLUE-DGA-EXT-WPG_SSL_VERSION_HEADER_INSERT_RULE': {'pools': [],
#                                                           'target_partition': 'TEST-WPG'},
#  '/WPG/BLUE-DGA-EXT-WPG_XFF_SERVER_SELECT_RULE': {'pools': [],
#                                                   'target_partition': 'TEST-WPG'},
#  '/WPG/BLUE-DGA-EXT-WP_WPG_PTE3_MACHINE_PERSIST_RULE': {'pools': [],
#                                                         'target_partition': ''}}
# VS_ADDRESS_DICT:
# {'/WPG/10.130.13.36': 'TEST-WPG'}
# POOL_DICT:
# {'/WPG/BLUE-DGA-EXT-WPG_PTE3_SECURETEST_POOL': 'TEST-WPG'}
#
for vs, vs_data in vs_dict.items():
    if 'pool' in vs_data.keys():
        if vs_data['pool'] not in pool_dict.keys():
            pool = vs_data['pool']
            pool_dict[pool] = vs_data['target_partition']
    if 'destination' in vs_data.keys():
        if vs_data['destination'] not in vs_address_dict.keys():
            vs_address = vs_data['destination']
            vs_address_dict[vs_address] = vs_data['target_partition']
    if 'rules' in vs_data.keys():
        for rule in vs_data['rules']:
            pools = rule_dict[rule]["pools"]
            rule_dict[rule]["target_partition"] = vs_data["target_partition"]
            for pool in pools:
                pool_dict[pool] = vs_data['target_partition']
if args.verbose:
    print("VS_DICT")
    pprint(vs_dict)
    print("RULE_DICT:")
    pprint(rule_dict)
    print("VS_ADDRESS_DICT:")
    pprint(vs_address_dict)
    print("POOL_DICT:")
    pprint(pool_dict)
    print()
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
        # if bracket == 1 and line[-1] == "{":
        if bracket == 1 and 'ltm' in line:
            object_header = line
    # print("BRACKET:", bracket)
    # print("HEADER:", object_header)
    # print("LINE":, line)
    # pool objects
    if object_header.startswith('ltm pool'):
        # Find/replace
        if line.startswith('ltm pool'):
            fq_pool_name = line.split(' ')[2]
            if fq_pool_name in pool_dict.keys():
                target_partition = pool_dict[fq_pool_name]
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(f"/{partition}/", f"/{target_partition}/")
            else:
                target_partition = ''
                partition = ''
        # Member have ":" in name
        if ':' in line and target_partition and partition:
            line = line.replace(f"/{partition}/", f"/{target_partition}/")
    # virtual-address objects
    elif object_header.startswith('ltm virtual-address'):
        if line.startswith('ltm virtual-address'):
            fq_virtual_address = line.split(' ')[2]
            if fq_virtual_address in vs_address_dict.keys():
                target_partition = vs_address_dict[fq_virtual_address]
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(f"/{partition}/", f"/{target_partition}/")
            else:
                target_partition = ''
                partition = ''
        line = line.replace('route-advertisement selective', 'route-advertisement disabled')
        line = line.replace('route-advertisement enabled', 'route-advertisement disabled')
        line = line.replace('route-advertisement always', 'route-advertisement disabled')
    # virtual objects
    elif object_header.startswith('ltm virtual '):
        if line.startswith('ltm virtual '):
            fq_virtual_server = line.split(' ')[2]
            if fq_virtual_server in vs_dict.keys():
                target_partition = vs_dict[fq_virtual_server]['target_partition']
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(f"/{partition}/", f"/{target_partition}/")
            else:
                target_partition = ''
                partition = ''
        elif 'destination' in line:
            if target_partition:
                line = line.replace(f"/{partition}/", f"/{target_partition}/")
        elif 'pool' in line and bracket == 1:
            if target_partition:
                line = line.replace(f"/{partition}/", f"/{target_partition}/")
        elif 'rules' in line and bracket == 2:
            object_subsection = 'RULE'
        elif object_subsection == 'RULE' and bracket > 1:
            rule = line.strip()
            partition = line.split('/')[1]
            if target_partition:
                line = line.replace(f"/{partition}/", f"/{target_partition}/")
        elif object_subsection == 'RULE' and bracket == 1:
            object_subsection = ''

    # rule objects
    elif object_header.startswith('ltm rule '):
        if line.startswith('ltm rule '):
            fq_rule_name = line.split(' ')[2]
            if fq_rule_name in rule_dict.keys():
                target_partition = rule_dict[fq_rule_name]["target_partition"]
                if target_partition:
                    partition = line.split('/')[1]
                    line = line.replace(f"/{partition}/", f"/{target_partition}/")
            else:
                target_partition = ""
                partition = ""
        elif 'set destpool' in line:
            pool = line.split('destpool')[1].replace('}', '').strip()
            partition = pool.split('/')[1]
            line = line.replace(f"/{partition}/", f"/{target_partition}/")


    fo.write(line)
fh.close()
fo.close()
