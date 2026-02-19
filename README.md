# F5 Config Mangler
This script reads an F5 configuration file and changes the virtual server partition according to a map file.
## Usage
```
python f5_mutate.py -h
usage: f5_mutate.py [-h] -m MAP [-i INPUT] [-o OUTPUT]

Change partition for F5 virtual servers

optional arguments:
  -h, --help            show this help message and exit
  -m MAP, --map MAP     Map file in partition_map directory
  -i INPUT, --input INPUT
                        Input F5 config file in configs directory
  -o OUTPUT, --output OUTPUT
                        Output file in output directory
```
## Map file format
Format of map YAML file:
```
"VIRTUAL_SERVER_NAME": "PARTITION_NAME"
```
## Configuration objects mutated
Script changes partition for:
```
ltm virtual NAME {
    destination NAME
    pool NAME
}

ltm virtual-address NAME {
    route-advertisement disabled
}

ltm pool NAME {
    members {
        NAME
    }
}

ltm rule NAME {
when HTTP_REQUEST {
                switch -glob [HTTP::path] {
                "/*" { set destpool NAME }
                }
        }
}
```
## Testing
```
python f5_mutate.py -m small-map.yml -i small-pool.txt -v
python f5_mutate.py -m small-map.yml -i small-rule.txt -v
```