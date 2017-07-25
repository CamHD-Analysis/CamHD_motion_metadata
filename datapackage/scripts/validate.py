from pprint import pprint
from goodtables import validate

report = validate('../datapackage.json')

pprint(report)
