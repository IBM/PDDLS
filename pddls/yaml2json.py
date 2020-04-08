import sys
import json
import yaml


def main():
    doc = yaml.load(open(sys.argv[1], 'r'))
    print(json.dumps(doc, indent=True))


if __name__ == '__main__':
    main()
