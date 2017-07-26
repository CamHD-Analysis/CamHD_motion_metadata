from pprint import pprint
from goodtables import validate

datapackage_file = "datapackage.json"

report = validate(datapackage_file)

pprint(report)


exit(0 if report['valid'] else 1)
