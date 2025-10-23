# Build Scripts for VGTECH Road Damage Detector

This directory contains scripts to build standalone installers for Linux and Windows.

## 📁 Contents

- `build-installer-linux.sh` - Linux build script (.tar.gz)
- `build-installer-windows.ps1` - Windows build script (.zip with .exe)

## 🚀 Usage

### Linux Build

```bash
cd jetson-road-damage
chmod +x build-scripts/build-installer-linux.sh
./build-scripts/build-installer-linux.sh
```

**Output:**
- `releases/vgtech-road-damage-detector-v{VERSION}-linux-x64.tar.gz`

**Requirements:**
- Python 3.8+
- Virtual environment support
- tar, gzip

### Windows Build

```powershell
cd jetson-road-damage
.\build-scripts\build-installer-windows.ps1
```

**Output:**
- `releases/vgtech-road-damage-detector-v{VERSION}-windows-x64.zip`

**Requirements:**
- Python 3.8+
- PowerShell 5.1+
- Windows 10/11

## 📦 What Gets Built

Both scripts create a standalone package containing:

1. **Executable** - Standalone app (no Python required for end users)
2. **Configuration** - `.env` template with examples
3. **Documentation** - README, CHANGELOG, QUICKSTART
4. **Launcher Scripts** - Easy run scripts (`run.sh` / `run.bat`)
5. **Models Directory** - Empty folder for TFLite model
6. **Data Directory** - For local database

## 🔄 Build Process

1. **Setup Environment**
   - Create/activate virtual environment
   - Install dependencies
   - Install PyInstaller

2. **Build Executable**
   - Use platform-specific `.spec` file
   - Bundle Python interpreter and dependencies
   - Create standalone binary

3. **Package Release**
   - Copy executable and dependencies
   - Add documentation and configs
   - Create launcher scripts
   - Generate archive (tar.gz or zip)

## 📋 Version Management

Version is read from `VERSION` file in project root.

To create a new release:

```bash
# Update version
echo "1.1.0" > VERSION

# Update CHANGELOG.md with new version notes

# Build
./build-scripts/build-installer-linux.sh
# or
.\build-scripts\build-installer-windows.ps1
```

## 🎯 Distribution

After building:

1. **Test the release**
   ```bash
   # Linux
   cd releases/vgtech-road-damage-detector-v{VERSION}-linux-x64
   ./run.sh

   # Windows
   cd releases\vgtech-road-damage-detector-v{VERSION}-windows-x64
   run.bat
   ```

2. **Upload to GitHub Releases**
   - Go to GitHub repository > Releases > Create new release
   - Tag version: `v{VERSION}` (e.g., `v1.0.0`)
   - Upload the `.tar.gz` (Linux) and `.zip` (Windows)
   - Copy changelog notes to release description

## 🐛 Troubleshooting

### Build Fails

**"PyInstaller not found"**
```bash
pip install pyinstaller
```

**"Module not found" during build**
- Add to `hiddenimports` in `.spec` file
- Rebuild

### Large Archive Size

- Remove unused dependencies from `requirements.txt`
- Exclude unnecessary files in `.spec` file
- Use `upx=True` for compression (already enabled)

### Runtime Errors

**"Failed to execute script"**
- Check logs in `road_damage_detector.log`
- Verify all dependencies in `.spec` file
- Test with `--debug` flag in PyInstaller

## 🔧 Customization

### Add Files to Release

Edit the build script to copy additional files:

```bash
# In build-installer-linux.sh or .ps1
cp your-file.txt "$RELEASE_DIR/"
```

### Modify Executable Settings

Edit platform-specific `.spec` files:
- `build-linux.spec` - Linux settings
- `build-windows.spec` - Windows settings

Key settings:
- `console=True` - Show console window
- `icon='icon.ico'` - Application icon
- `upx=True` - Compress with UPX
- `hiddenimports` - Additional Python modules

## 📚 Related Files

- `../VERSION` - Current version number
- `../CHANGELOG.md` - Version history
- `../build-linux.spec` - Linux PyInstaller config
- `../build-windows.spec` - Windows PyInstaller config
- `../.env.example` - Configuration template

## 🆘 Support

For issues:
1. Check `TROUBLESHOOTING.md` in main directory
2. Review build logs
3. Test in virtual environment first
4. Check PyInstaller documentation: https://pyinstaller.org/

## 📝 Notes

- **Linux builds** can only be created on Linux
- **Windows builds** can only be created on Windows
- **macOS builds** would need a separate `.spec` and build script
- Models are NOT included in the release (too large)
- Users must provide their own `.tflite` model file
