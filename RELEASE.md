# Release Process Documentation

This document describes how to create and publish releases for VGTECH Road Damage Detector.

## 📋 Quick Reference

### Version Format
We use [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR** (1.x.x): Breaking changes, incompatible API changes
- **MINOR** (x.1.x): New features, backwards-compatible
- **PATCH** (x.x.1): Bug fixes, backwards-compatible

### Release Checklist

- [ ] Update `VERSION` file
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Commit changes: `git commit -m "Release v1.x.x"`
- [ ] Create and push tag: `git tag v1.x.x && git push origin v1.x.x`
- [ ] Wait for GitHub Actions to build releases (automatic)
- [ ] Download and test the release artifacts
- [ ] Publish release notes on GitHub

## 🚀 Creating a Release

### Method 1: Automated (Recommended)

GitHub Actions will automatically build and publish releases when you push a version tag.

```bash
# 1. Update version number
echo "1.1.0" > VERSION

# 2. Update CHANGELOG.md
# Add a new section:
## [1.1.0] - 2025-10-24
### Added
- New feature X
### Fixed
- Bug Y

# 3. Commit changes
git add VERSION CHANGELOG.md
git commit -m "Release v1.1.0"

# 4. Create and push tag
git tag v1.1.0
git push origin main
git push origin v1.1.0

# 5. GitHub Actions will automatically:
#    - Build Linux x64 executable
#    - Build Windows x64 executable
#    - Create GitHub Release
#    - Upload artifacts (.tar.gz and .zip)
```

**GitHub Actions Workflow:**
- Triggers on tags matching `v*.*.*`
- Builds on Ubuntu (Linux) and Windows runners
- Extracts changelog for release notes
- Creates standalone installers with launchers
- Uploads to GitHub Releases automatically

### Method 2: Manual Build

If you need to build locally (for testing or custom builds):

#### Linux

```bash
cd jetson-road-damage

# Build using installer script
chmod +x build-scripts/build-installer-linux.sh
./build-scripts/build-installer-linux.sh

# Or manually with PyInstaller
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build-linux.spec
```

**Output:** `releases/vgtech-road-damage-detector-v{VERSION}-linux-x64.tar.gz`

#### Windows

```powershell
cd jetson-road-damage

# Build using installer script
.\build-scripts\build-installer-windows.ps1

# Or manually with PyInstaller
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
pyinstaller build-windows.spec
```

**Output:** `releases/vgtech-road-damage-detector-v{VERSION}-windows-x64.zip`

## 📦 Release Contents

Each release archive includes:

### Files
- `road-damage-detector` / `road-damage-detector.exe` - Standalone executable
- `run.sh` / `run.bat` - Launcher scripts with environment checks
- `.env` - Configuration template
- `VERSION` - Version number
- `README.md` - Full documentation
- `CHANGELOG.md` - Version history
- `QUICKSTART.md` - Quick start guide
- `README-RELEASE.txt` - Release-specific quick start

### Directories
- `models/` - Empty directory for TFLite model (user-provided)
- `data/` - Local SQLite database storage
- `_internal/` - Python runtime and dependencies (PyInstaller bundle)

## 🔍 Testing a Release

Before publishing:

### Linux Testing
```bash
# Extract
tar -xzf vgtech-road-damage-detector-v1.0.0-linux-x64.tar.gz
cd vgtech-road-damage-detector-v1.0.0-linux-x64

# Configure
cp .env.example .env
nano .env  # Edit with your settings

# Copy model
cp /path/to/model.tflite models/

# Run
./run.sh
```

### Windows Testing
```powershell
# Extract .zip file
cd vgtech-road-damage-detector-v1.0.0-windows-x64

# Configure
Copy-Item .env.example .env
notepad .env  # Edit with your settings

# Copy model
Copy-Item C:\path\to\model.tflite models\

# Run
.\run.bat
```

### Verification Checklist
- [ ] Launcher script validates .env file
- [ ] Launcher script checks for model file
- [ ] Application starts without errors
- [ ] Camera detection works (if cameras available)
- [ ] Database initialization succeeds
- [ ] UI displays correctly
- [ ] Version number shows in logs/UI
- [ ] Supabase sync works (if configured)

## 📝 Release Notes Template

Use this template in `CHANGELOG.md`:

```markdown
## [1.x.x] - YYYY-MM-DD

### Added
- New feature descriptions
- New UI components
- New configuration options

### Changed
- Modifications to existing features
- Performance improvements
- Dependency updates

### Fixed
- Bug fix descriptions
- Issue resolutions

### Removed
- Deprecated features removed
- Unused dependencies removed

### Security
- Security vulnerability fixes
- CVE resolutions
```

## 🌐 Publishing on GitHub

### After Automated Build

1. **Go to GitHub Releases**
   - Navigate to: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
   - Find the automatically created release

2. **Verify Release**
   - Check that both Linux and Windows artifacts are attached
   - Verify changelog notes are correct
   - Ensure tag matches VERSION file

3. **Edit if Needed**
   - Add screenshots or demo videos
   - Add upgrade instructions
   - Highlight breaking changes

4. **Publish**
   - Release is already published by GitHub Actions
   - Share release URL with users

### Manual Release (if needed)

```bash
# Using GitHub CLI
gh release create v1.0.0 \
  releases/vgtech-road-damage-detector-v1.0.0-linux-x64.tar.gz \
  releases/vgtech-road-damage-detector-v1.0.0-windows-x64.zip \
  --title "VGTECH Road Damage Detector v1.0.0" \
  --notes-file CHANGELOG.md
```

## 🔄 Version Management

### When to Bump Versions

**MAJOR (1.x.x → 2.0.0)**
- Breaking changes to .env configuration
- Incompatible database schema changes
- Major UI/UX redesign
- Platform support changes (e.g., drop Python 3.8)

**MINOR (x.1.x → x.2.0)**
- New features (e.g., new damage class)
- New configuration options (backwards-compatible)
- New measurement algorithms
- Performance improvements
- New platform support

**PATCH (x.x.1 → x.x.2)**
- Bug fixes
- Security patches
- Documentation updates
- Dependency updates (minor)
- UI polish without new features

### Pre-release Versions

For testing or beta releases:

```bash
# Alpha
echo "1.1.0-alpha.1" > VERSION
git tag v1.1.0-alpha.1

# Beta
echo "1.1.0-beta.1" > VERSION
git tag v1.1.0-beta.1

# Release Candidate
echo "1.1.0-rc.1" > VERSION
git tag v1.1.0-rc.1
```

## 🐛 Troubleshooting Release Builds

### GitHub Actions Fails

**Check logs:**
```bash
# View workflow runs
gh run list --workflow=release.yml

# View specific run logs
gh run view RUN_ID --log
```

**Common issues:**
- Missing dependencies in requirements.txt
- PyInstaller spec file errors
- File not found during packaging
- Permissions issues

### Build Size Too Large

**Reduce size:**
```python
# In build-*.spec, add excludes:
excludes=['tkinter', 'matplotlib', 'scipy']
```

**Enable UPX compression:**
```python
# Already enabled in spec files:
upx=True,
```

### Icon Not Showing

**Windows:**
- Ensure `icon.ico` exists
- Rebuild with: `python create_icon.py`
- Check `build-windows.spec` has: `icon='icon.ico'`

**Linux:**
- Desktop entry requires separate .desktop file
- Icon handled by desktop environment

## 📚 Related Documentation

- `build-scripts/README.md` - Build script documentation
- `CHANGELOG.md` - Version history
- `QUICKSTART.md` - Quick start guide
- `.github/workflows/release.yml` - CI/CD configuration

## 🆘 Support

For release-related issues:

1. Check GitHub Actions logs
2. Test build locally first
3. Verify PyInstaller version compatibility
4. Check platform-specific requirements
5. Review PyInstaller documentation: https://pyinstaller.org/

## 📄 License

Releases inherit the project license. Ensure LICENSE file is included in all release archives.
