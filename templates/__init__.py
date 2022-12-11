import json
import os

path = os.path.join(os.path.dirname(__file__), 'SubWorldData.json')

if os.path.exists(path) is False:
	raise Exception('SubWorldData template was not found')

with open(path, 'r') as f:
	subWorldDataTemp = json.load(f)

path = os.path.join(os.path.dirname(__file__), 'ObjectBlueprint.json')

if os.path.exists(path) is False:
	raise Exception('ObjectBlueprint template was not found')

with open(path, 'r') as f:
	objectBlueprintTemp = json.load(f)

path = os.path.join(os.path.dirname(__file__), 'ReferenceObjectData.json')

if os.path.exists(path) is False:
	raise Exception('ReferenceObjectData template was not found')

with open(path, 'r') as f:
	referenceObjectDataTemp = json.load(f)

path = os.path.join(os.path.dirname(__file__), 'EffectReferenceObjectData.json')

if os.path.exists(path) is False:
	raise Exception('EffectReferenceObjectData template was not found')

with open(path, 'r') as f:
	effectReferenceObjectDataTemp = json.load(f)
