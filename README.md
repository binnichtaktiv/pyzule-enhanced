# pyzule
an [azule](https://github.com/Al4ise/Azule) "clone" written in python3. windows is not currently supported, but it should *(hopefully)* work in wsl.

## features
not many right now, but will probably add some in the future if i need them.

- inject deb, dylib, framework, bundle, and appex files and automatically fix dependencies when possible
- remove UISupportedDevices
- remove watch app

## installation

### requirements

#### cli tools
you need `git`, `gcc`, `zip`, and `tar`. you also need `ar` if you're on linux.

#### insert_dylib
you have to build this yourself.

`git clone https://github.com/tyilo/insert_dylib.git && cd insert_dylib/insert_dylib && gcc main.c && chmod +x a.out && sudo mv a.out /usr/local/bin/insert_dylib && cd ../.. && sudo rm -r insert_dylib`

if you're on macos, that should be everything you need to install. skip to the installation script.

#### install_name_tool
installed by default on macos. tested on an amd64 linux machine, it probably won't work on anything else. i don't know where to get the binaries for other architectures.

`sudo wget https://cdn.discordapp.com/attachments/1105232452529700985/1117486649803292837/install_name_tool -O /usr/local/bin/install_name_tool && sudo chmod +x /usr/local/bin/install_name_tool`

#### ldid
also installed by default on macos.

`sudo wget https://cdn.discordapp.com/attachments/1105232452529700985/1117486650184978433/ldid -O /usr/local/bin/ldid && sudo chmod +x /usr/local/bin/ldid`

#### otool
ALSO installed by default on macos. (who could've guessed?!)

`sudo wget https://cdn.discordapp.com/attachments/1105232452529700985/1117486650533085275/otool -O /usr/local/bin/otool && sudo chmod +x /usr/local/bin/otool`

### installation script
required. will install pyzule itself.

`curl https://raw.githubusercontent.com/asdfzxcvbn/pyzule/main/install-pyzule.py | python3 || python`

> **isn't that unsafe?**
> 
> pretty much. if you're that paranoid, then you should know how to do it manually.

## contributing

### code
if you'd like to improve `pyzule`, then fork this repo and open a PR to the `dev` branch. thank you!

### money
if you want to support [my work](https://github.com/asdfzxcvbn?tab=repositories), you can donate me some monero! any donations are GREATLY appreciated. :)

xmr address: `82m19F4yb15UQbJUrxxmzJ3fvKyjjqJM55gv8qCp2gSTgo3D8avzNJJQ6tREGVKA7VUUJE6hPKg8bKV6tTXKhDDx75p6vGj`

qr code:

![qr](https://user-images.githubusercontent.com/109937991/227786784-28eaf0a1-9d17-4fc5-8c1c-f017fd62cfad.png)

## credits
`pyzule` wouldn't be possible if it wasn't for the work of some marvelous people. HUGE thanks to:

- [Al4ise](https://github.com/Al4ise) for [Azule](https://github.com/Al4ise/Azule)
- [tyilo](https://github.com/tyilo) for [insert_dylib](https://github.com/tyilo/insert_dylib)