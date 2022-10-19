import json
import os

path = os.path.join(os.getcwd(), 'templates', 'SubWorldData.json')

if os.path.exists(path) is False:
    error('SubWorldData template was not found')

with open(path, 'r') as f:
	subWorldDataTemp = json.loads(f.read())

path = os.path.join(os.getcwd(), 'templates', 'ObjectBlueprint.json')

if os.path.exists(path) is False:
    error('ObjectBlueprint template was not found')

with open(path, 'r') as f:
    objectBlueprintTemp = json.loads(f.read())

path = os.path.join(os.getcwd(), 'templates', 'ReferenceObjectData.json')

if os.path.exists(path) is False:
    error('ReferenceObjectData template was not found')

with open(path, 'r') as f:
    referenceObjectDataTemp = json.loads(f.read())

path = os.path.join(os.getcwd(), 'templates', 'EffectReferenceObjectData.json')

if os.path.exists(path) is False:
    error('EffectReferenceObjectData template was not found')

with open(path, 'r') as f:
    effectReferenceObjectDataTemp = json.loads(f.read())
