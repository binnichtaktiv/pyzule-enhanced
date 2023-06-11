#!/Library/Frameworks/Python.framework/Versions/3.10/bin/python3
import argparse
import sys
import os
from shutil import rmtree, copyfile, copytree, move
from subprocess import run, DEVNULL
from plistlib import load, dump
from platform import system
from zipfile import ZipFile
from time import time
from glob import glob
WORKING_DIR = os.getcwd()
USER_DIR = os.path.expanduser("~/.zxcvbn")
changed = 0

# check os compatibility and set 
system = system()
if system == "Windows":
    print("windows is not currently supported.")
    sys.exit(1)
elif system == "Linux":
    otool = "llvm-otool"
else:
    otool = "otool"

# set/get all args
parser = argparse.ArgumentParser(description="an azule \"clone\" written in python3.")
parser.add_argument("-i", metavar="ipa", type=str, required=True,
                    help="the ipa to patch")
parser.add_argument("-o", metavar="output", type=str, required=True,
                    help="the name of the patched ipa that will be outputted")
parser.add_argument("-f", metavar="files", nargs="+", type=str,
                    help="tweak files to inject into the ipa")
parser.add_argument("-u", action="store_true",
                    help="remove UISupportedDevices")
parser.add_argument("-w", action="store_true",
                    help="remove watch app")
args = parser.parse_args()

# checking received args
if not args.i.endswith(".ipa") or not args.o.endswith(".ipa"):
    parser.error("the input and output file must be an ipa")
elif not os.path.exists(args.i):
    parser.error(f"{args.i} does not exist")
elif not (args.f or args.u or args.w):
    parser.error("at least one option to modify the ipa must be present")


def cleanup(extract_dir, success):
    rmtree(extract_dir)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


# extracting ipa
print("[*] extracting ipa..")
EXTRACT_DIR = f".pyzule-{time()}"
with ZipFile(args.i, "r") as ipa:
    ipa.extractall(path=EXTRACT_DIR)
print("[*] extracted ipa successfully")

# checking if everything exists (to see if it's a valid ipa)
try:
    APP_PATH = glob(f"{EXTRACT_DIR}/Payload/*.app")[0]
    PLIST_PATH = glob(f"{APP_PATH}/Info.plist")[0]
except IndexError:
    print("[!] couldn't find Payload folder and/or Info.plist file, invalid ipa specified")
    cleanup(EXTRACT_DIR, False)


# injecting stuff
if args.f:
    with open(PLIST_PATH, "rb") as pl:
        BINARY = load(pl)["CFBundleExecutable"]
    if any(i.endswith(".appex") for i in args.f):
        os.makedirs(f"{APP_PATH}/PlugIns", exist_ok=True)
    if any(i.endswith(known) for i in args.f for known in (".deb", ".dylib", ".framework")):
        os.makedirs(f"{APP_PATH}/Frameworks", exist_ok=True)
        deb_counter = 0
    dylibs = [d for d in args.f if d.endswith(".dylib")]
    id = dylibs + [f for f in args.f if ".framework" in f]
    remove = []

    # extracting all debs
    for deb in args.f:
        if not deb.endswith(".deb"):
            continue
        print(f"[*] extracting {deb}..")
        output = f"{EXTRACT_DIR}/{deb_counter}"
        os.makedirs(output)
        os.makedirs(f"{output}/e")
        if system == "Linux":
            run(["ar", "-x", deb, f"--output={output}"])
        else:
            run(["tar", "-xf", deb, "-C", output])
        data_tar = glob(f"{output}/data.*")[0]
        run(["tar", "-xf", data_tar, "-C", f"{output}/e"])
        for dirpath, dirnames, filenames in os.walk(f"{output}/e"):
            for filename in filenames:
                if filename.endswith(".dylib"):
                    src_path = os.path.join(dirpath, filename)
                    dest_path = os.path.join(WORKING_DIR, filename)
                    move(src_path, dest_path)
                    dylibs.append(filename)
                    id.append(filename)
                    remove.append(filename)
            for dirname in dirnames:
                if dirname.endswith(".bundle") or dirname.endswith(".framework"):
                    src_path = os.path.join(dirpath, dirname)
                    dest_path = os.path.join(WORKING_DIR, dirname)
                    move(src_path, dest_path)
                    args.f.append(dirname)
                    if ".framework" in dirname:
                        id.append(dirname)
                    remove.append(dirname)
        print(f"[*] extracted {deb} successfully")
        deb_counter += 1

    # removing codesign from all dylibs
    for dylib in dylibs:
        run(["ldid", "-S", dylib], stdout=DEVNULL)

    # fix all dependencies (except substrate lol)
    for dylib in dylibs:
        deps_temp = run(["otool", "-L", dylib], capture_output=True, text=True).stdout.strip().split("\n")[2:]
        for ind, dep in enumerate(deps_temp):
            if "(architecture arm64" in dep:
                deps_temp = deps_temp[:ind]
                break
            
        deps = [dep.split()[0] for dep in deps_temp if dep.startswith("\t/Library/")] + [dep.split()[0] for dep in deps_temp if dep.startswith("\t/usr/lib/")]
        
        for dep in deps:
            for known in id:
                if known in dep:
                    bn = os.path.basename(dep)
                    if dep.endswith(".dylib"):
                        fni = dep.find(bn)
                        run(["install_name_tool", "-change", f"{dep[:fni]}{bn}", f"@rpath/{bn}", dylib])
                        print(f"[*] fixed dependency in {dylib}: {dep[:fni]}{bn} -> @rpath/{bn}")
                    elif ".framework" in dep:
                        fni = dep.find(f"{bn}.framework/{bn}")
                        run(["install_name_tool", "-change", f"{dep[:fni]}{bn}.framework/{bn}", f"@rpath/{bn}.framework/{bn}", dylib])
                        print(f"[*] fixed dependency in {dylib}: {dep[:fni]}{bn}.framework/{bn} -> @rpath/{bn}.framework/{bn}")

    # fixing cydiasubstrate
    for dylib in dylibs:
        run(["install_name_tool", "-change", "/Library/Frameworks/CydiaSubstrate.framework/CydiaSubstrate", "@rpath/CydiaSubstrate.framework/CydiaSubstrate", dylib])
        run(["install_name_tool", "-change", "@executable_path/libsubstrate.dylib", "@rpath/CydiaSubstrate.framework/CydiaSubstrate", dylib])  # some dylibs have this
    copytree(f"{USER_DIR}/CydiaSubstrate.framework", f"{APP_PATH}/Frameworks/CydiaSubstrate.framework")

    print("[*] injecting..")
    for d in dylibs:
        run(["insert_dylib", "--inplace", "--no-strip-codesig", f"@rpath/{d}", f"{APP_PATH}/{BINARY}"], stdout=DEVNULL)
        copyfile(d, f"{APP_PATH}/Frameworks/{d}")
        print(f"[*] successfully injected {d}")
    for tweak in args.f:
        if tweak.endswith(".framework"):
            copytree(tweak, f"{APP_PATH}/Frameworks/{tweak}")
            print(f"[*] successfully injected {tweak}")
        elif tweak.endswith(".bundle"):
            copytree(tweak, f"{APP_PATH}/{tweak}")
            print(f"[*] successfully copied {tweak} to app root")
        elif tweak.endswith(".appex"):
            copytree(tweak, f"{APP_PATH}/PlugIns/{tweak}")
            print(f"[*] successfully copied {tweak} to PlugIns")
    changed = 1

    for r in remove:
        if os.path.isfile(r):
            os.remove(r)
        else:
            rmtree(r)

# removing UISupportedDevices (if specified)
if args.u:
    print("[*] removing UISupportedDevices..")
    with open(PLIST_PATH, "rb") as p:
        plist = load(p)
    
    if "UISupportedDevices" in plist:
        del plist["UISupportedDevices"]
        print("[*] removed UISupportedDevices")
        changed = 1
        with open(PLIST_PATH, "wb") as p:
            dump(plist, p)
    else:
        print("[?] UISupportedDevices not present")

# removing watch app (if specified)
if args.w:
    print("[*] removing watch app..")
    try:
        rmtree(f"{APP_PATH}/Watch")
        print("[*] removed watch app")
        changed = 1
    except FileNotFoundError:
        print("[?] watch app not present")

# checking if anything was actually changed
if not changed:
    print("[!] nothing was changed, output file will not be created")
    cleanup(EXTRACT_DIR, True)

# zipping everything back into an ipa
os.chdir(EXTRACT_DIR)
print("[*] generating ipa..")
run(["zip", "-3", "-r", f"{WORKING_DIR}/{args.o}", "Payload"], stdout=DEVNULL)

# cleanup when everything is done
os.chdir(WORKING_DIR)
cleanup(EXTRACT_DIR, True)