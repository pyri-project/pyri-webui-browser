# Build and copy package wheel to the current pyri.webui_server wheel directory

import subprocess
import re
import glob
import shutil
import appdirs
from pathlib import Path

def main():
    with open("setup.py","r") as f:
        setup_py_text = f.read()
        #Make sure in the correct directory
        assert "name='pyri-webui-browser'" in setup_py_text

        version_match = re.search(r"version\s*=\s*'(\d+\.\d+\.\d+)'",setup_py_text)
        assert version_match is not None
        version = version_match.group(1)
    print(version)

    subprocess.check_call("python setup.py bdist_wheel",shell=True)

    wheel_fname = Path(glob.glob(f"dist/pyri_webui_browser-{version}*.whl")[0])
    wheels_dir = Path(appdirs.user_data_dir(appname="pyri-webui-server", appauthor="pyri-project", roaming=False)).joinpath("wheels").joinpath(wheel_fname.name)
    shutil.copyfile(wheel_fname,wheels_dir)
    print(f"Copied wheel version {version} to {str(wheels_dir)}")

if __name__ == "__main__":
    main()
