[app]
title = Eslatmalar
package.name = eslatmalar
package.domain = uz.mingqulova.rayhona
source.dir = .
source.include_exts = py,png,kv,json
source.exclude_dirs = tests,.venv,__pycache__,.git
version = 1.0.0
requirements = python3,kivy==2.3.1
orientation = portrait
fullscreen = 0
icon.filename = assets/app_icon.png
presplash.filename = assets/app_icon.png
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True
android.private_storage = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
