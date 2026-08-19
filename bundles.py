import json
import os
import subprocess

WIN32_PREFIX = 'Win32'
BUNDLE_PREFIX = 'CustomLevels'
FROSTBITE_VER = 'Frostbite2_0'
INTERMEDIATE_FOLDER_NAME = 'intermediate'
EBX_JSON_FOLDER_NAME = 'ebx_json'
SB_OUTPUT_FOLDER_NAME = 'sb'

def generate_bundles(rime_path: str, out_dir: str):
	input_path = os.path.join(
		os.getcwd(), INTERMEDIATE_FOLDER_NAME, EBX_JSON_FOLDER_NAME)
	# ABSOLUTE, because this path is handed to Rime and Rime is run with cwd=rime_path (see the
	# subprocess call at the end of this function). A relative -o/--output therefore resolved
	# against Rime's own directory: the superbundle was written to <rime>/mods/<name>/sb/ and the
	# generated mod shipped with an EMPTY sb/ — a level loader with no content, and no error
	# anywhere, since Rime reported "Superbundle successfully built!" for the copy it did write.
	output_path = os.path.abspath(os.path.join(out_dir, SB_OUTPUT_FOLDER_NAME))

	if not os.path.exists(output_path):
		os.makedirs(output_path)
	commands = []

	super_bundle_names = []
	print('Superbundles:')

	commands_path = os.path.join(os.getcwd(), INTERMEDIATE_FOLDER_NAME, 'commands.txt')

	for mapName in os.listdir(input_path):
		# build superbundle
		sb_name = WIN32_PREFIX + '/' + BUNDLE_PREFIX + '/' + mapName + '/' + mapName
		commands.append('build_sb ' + sb_name + ' ' +
						FROSTBITE_VER + ' \"' + output_path + '\"\n')

		for file in os.listdir(os.path.join(input_path, mapName)):
			file_name = os.path.splitext(file)[0]  # Remove extension
			file_path = os.path.join(input_path, mapName, file)

			if not os.path.isfile(file_path):
				continue

			# build bundle
			bundle_name_w32 = WIN32_PREFIX + '/' + BUNDLE_PREFIX + '/' + mapName + '/' + file_name
			commands.append('build_bundle ' + bundle_name_w32 + '\n')

			partition_name = BUNDLE_PREFIX + '/' + mapName + '/' + file_name

			# add partition to bundle and build bundle
			commands.append('add_json_partition ' + partition_name.lower() + ' \"' + file_path + '\"\n')

			# Extra partitions that must live in THIS bundle rather than one of their own — the
			# level is patched with a SubWorldReferenceObjectData naming a single bundle, so
			# anything in a separate bundle is never loaded and objects referencing it vanish.
			sidecar_path = os.path.join(input_path, mapName, file_name + '.d')

			if os.path.isdir(sidecar_path):
				for sidecar_file in sorted(os.listdir(sidecar_path)):
					if not sidecar_file.endswith('.json'):
						continue

					sidecar_partition = BUNDLE_PREFIX + '/' + mapName + '/' + os.path.splitext(sidecar_file)[0]
					commands.append('add_json_partition ' + sidecar_partition.lower() + ' \"'
									+ os.path.join(sidecar_path, sidecar_file) + '\"\n')

			# Shadow partitions replace a STOCK partition, so they keep its own name rather than
			# getting a CustomLevels one — that is what makes every existing reference resolve to
			# ours. The name lives in the file (Name), since a partition name contains slashes and
			# cannot be carried in a filename.
			shadow_path = os.path.join(input_path, mapName, file_name + '.shadow.d')

			if os.path.isdir(shadow_path):
				for shadow_file in sorted(os.listdir(shadow_path)):
					if not shadow_file.endswith('.json'):
						continue

					shadow_full = os.path.join(shadow_path, shadow_file)

					with open(shadow_full, 'r') as f:
						shadow_name = json.load(f).get('Name', '')

					if not shadow_name:
						continue

					commands.append('add_json_partition ' + shadow_name.lower() + ' \"' + shadow_full + '\"\n')

			commands.append('build\n')

		# build superbundle
		commands.append('build\n\n')
		super_bundle_names.append(sb_name)
		print(sb_name)

	# save commands in commands.txt
	with open(commands_path, "w") as f:
		f.writelines(commands)

	print('Attempting to compile with Rime...')

	# execute commands with rime
	subprocess.run([os.path.join(rime_path, 'RimeREPL.exe'), commands_path], cwd=rime_path)

	return super_bundle_names
