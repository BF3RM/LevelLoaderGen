import argparse
import os

import exb_json
import bundles
import mod_generator

if __name__ == "__main__":
	try:
		# set it up
		parser = argparse.ArgumentParser(
			description='[--rimepath] RimeREPL.exe path')
		parser.add_argument("name", type=str, help="Name of the generated level loader mod, eg. rm-levelloader")
		parser.add_argument("version", type=str, help="Version of the generated level loader mod, eg. 1.0.0")
		parser.add_argument("-o", "--outputpath", type=str, help="Path where the generated mod should be placed")
		parser.add_argument("--rimepath", type=str, default='RimeREPL',
							help="Path to RimeREPL.exe. By default it uses rimeREPL as window\'s environment var")

		# get it
		args = parser.parse_args()
		rimePath = args.rimepath

		mod_name = args.name
		mod_version = args.version
		out_dir = args.outputpath
		if out_dir is None:
			out_dir = os.path.join(os.getcwd(), args.name)

		print("Generating mod {} of version {} in {}".format(mod_name, mod_version, out_dir))

		exb_json.generate_ebx_json(out_dir)
		superbundle_names = bundles.generate_bundles(rimePath, out_dir)
		mod_generator.generate_mod(mod_name, mod_version, superbundle_names, out_dir)
	except KeyboardInterrupt:
		print('User has exited the program')
