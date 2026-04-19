"""
UnblockCord -- PyInstaller Build Script
Tek .exe dosyasi uretir (Python kurulumu gerekmez).

Kullanim:
    python build.py
"""

import subprocess
import sys
import os
import shutil

# --- Ayarlar ---
APP_NAME    = "UnblockCord"
ENTRY_POINT = "main.py"
ICON_PATH   = os.path.join("assets", "icon.png")
DIST_DIR    = "dist"
BUILD_DIR   = "build"


def main():
    print("=" * 55)
    print(f"  {APP_NAME} -- Build Script")
    print("=" * 55 + "\n")

    # PyInstaller kurulu mu?
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[!] PyInstaller bulunamadi. Kuruluyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Eski dist/build klasorlerini temizle (exe aciksa atla)
    for folder in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"[ok] Temizlendi: {folder}/")
            except PermissionError:
                print(f"[!] {folder}/ silinemedi (dosya acik olabilir) — devam ediliyor.")

    # PyInstaller argumanlari
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--clean",
        "--add-data", f"assets{os.pathsep}assets",
    ]

    if os.path.exists(ICON_PATH):
        args += ["--icon", ICON_PATH]

    # UAC manifest -- yonetici yetkisi ister
    args += ["--uac-admin"]

    args.append(ENTRY_POINT)

    print("[>>] PyInstaller calistiriliyor...\n")
    result = subprocess.run(args)

    if result.returncode == 0:
        exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
        size_mb  = os.path.getsize(exe_path) / (1024 * 1024) if os.path.exists(exe_path) else 0
        print("\n" + "=" * 55)
        print("  [OK] Build basarili!")
        print(f"  Cikti : {exe_path}")
        print(f"  Boyut : {size_mb:.1f} MB")
        print("=" * 55)
    else:
        print(f"\n[HATA] Build basarisiz! Hata kodu: {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
