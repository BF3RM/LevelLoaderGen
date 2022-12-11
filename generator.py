import argparse
import exb_json
import bundles

if __name__ == "__main__":
    try:
        # set it up
        parser = argparse.ArgumentParser(
            description='[--rimepath] RimeREPL.exe path')
        parser.add_argument("--rimepath", type=str, default='RimeREPL',
                            help="Path to RimeREPL.exe. By default it uses rimeREPL as window\'s environment var")

        # get it
        args = parser.parse_args()
        rimePath = args.rimepath
        # print('Parsed arguments')

        exb_json.GenerateEbxJson()
        bundles.GenerateBundles(rimePath)
    except KeyboardInterrupt:
        print('User has exited the program')
