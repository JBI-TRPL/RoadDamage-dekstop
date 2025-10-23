# GitHub Actions & Release Automation - Quick Guide

## ✅ What's Been Set Up

### 1. 🎨 Application Icon
- **File:** `icon.ico` (multi-resolution: 256px → 16px)
- **Design:** Road damage theme with blue background
- **Preview:** `icon_preview.png`
- **Generator:** `create_icon.py` (run with: `python create_icon.py`)
- **Windows build:** Automatically includes icon in `.exe`

### 2. 🤖 GitHub Actions Workflow
- **File:** `.github/workflows/release.yml`
- **Trigger:** Push version tags (e.g., `v1.0.0`)
- **Manual trigger:** Available via GitHub Actions tab

### 3. 📦 Automated Build Process
- **Linux:** Builds on `ubuntu-latest` runner
- **Windows:** Builds on `windows-latest` runner
- **Both create:** Standalone installers with launchers and documentation

## 🚀 How to Create a Release

### Step 1: Update Version
```bash
cd jetson-road-damage
echo "1.1.0" > VERSION
```

### Step 2: Update Changelog
Edit `CHANGELOG.md`:
```markdown
## [1.1.0] - 2025-10-24
### Added
- GitHub Actions automated releases
- Windows application icon
### Changed
- Improved build process
```

### Step 3: Commit and Tag
```bash
git add VERSION CHANGELOG.md icon.ico .github/
git commit -m "Release v1.1.0: Add automated releases and icon"
git push origin main

# Create and push tag
git tag v1.1.0
git push origin v1.1.0
```

### Step 4: Watch Automation ✨
GitHub Actions will automatically:
1. ✅ Create release on GitHub
2. ✅ Build Linux x64 installer
3. ✅ Build Windows x64 installer (with icon!)
4. ✅ Upload `.tar.gz` and `.zip` files
5. ✅ Add changelog to release notes

### Step 5: Test & Publish
1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
2. Download and test the artifacts
3. Edit release if needed (add screenshots, etc.)
4. Share with users!

## 📋 Workflow Details

### What Happens When You Push a Tag

```
v1.1.0 tag pushed
    ↓
┌─────────────────────────────────────┐
│  Job 1: create-release              │
│  - Extract version from VERSION     │
│  - Extract changelog notes          │
│  - Create GitHub Release            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 2: build-linux (parallel)      │
│  - Setup Python 3.10                │
│  - Install dependencies             │
│  - Run PyInstaller                  │
│  - Package with run.sh              │
│  - Create .tar.gz                   │
│  - Upload to release                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 3: build-windows (parallel)    │
│  - Setup Python 3.10                │
│  - Install dependencies             │
│  - Generate icon (if missing)       │
│  - Run PyInstaller with icon        │
│  - Package with run.bat/ps1         │
│  - Create .zip                      │
│  - Upload to release                │
└─────────────────────────────────────┘
```

### Build Time
- **Linux:** ~5-8 minutes
- **Windows:** ~8-12 minutes
- **Total:** ~12-15 minutes from tag push to release

## 🎯 Release Artifacts

### Linux Archive
```
vgtech-road-damage-detector-v1.1.0-linux-x64.tar.gz
├── road-damage-detector-linux/
│   ├── road-damage-detector (executable)
│   └── _internal/ (Python runtime)
├── run.sh (launcher with checks)
├── .env (template)
├── VERSION
├── README.md
├── CHANGELOG.md
├── QUICKSTART.md
├── README-RELEASE.txt
├── models/ (empty - user provides)
└── data/ (empty - created on first run)
```

### Windows Archive
```
vgtech-road-damage-detector-v1.1.0-windows-x64.zip
├── road-damage-detector-windows/
│   ├── road-damage-detector.exe (with icon!)
│   └── _internal/ (Python runtime)
├── run.bat (batch launcher)
├── run.ps1 (PowerShell launcher)
├── .env (template)
├── VERSION
├── README.md
├── CHANGELOG.md
├── QUICKSTART.md
├── README-RELEASE.txt
├── models/ (empty - user provides)
└── data/ (empty - created on first run)
```

## 🔧 Manual Trigger

If you need to rebuild without creating a new tag:

1. Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
2. Select "Build and Release" workflow
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

## 🐛 Troubleshooting

### Workflow Fails
```bash
# View logs
gh run list --workflow=release.yml
gh run view RUN_ID --log

# Common fixes:
# - Check requirements.txt is up to date
# - Verify .spec files are valid
# - Ensure VERSION file exists
# - Check CHANGELOG.md format
```

### Icon Not Appearing
```bash
# Regenerate icon
python create_icon.py

# Verify in spec file
grep "icon=" build-windows.spec
# Should show: icon='icon.ico',

# Rebuild
git add icon.ico build-windows.spec
git commit -m "Update icon"
git tag v1.1.1
git push origin v1.1.1
```

### Large Build Size
```python
# In build-*.spec, add excludes:
excludes=[
    'tkinter',
    'matplotlib',
    'scipy',
    'IPython',
],
```

## 📚 Documentation Files

All documentation for releases:

1. **RELEASE.md** - Full release process guide (you are here!)
2. **build-scripts/README.md** - Build scripts documentation
3. **CHANGELOG.md** - Version history
4. **.github/workflows/release.yml** - CI/CD configuration

## 🎓 Best Practices

### Version Numbering
- **1.0.0** → **1.0.1**: Bug fixes only
- **1.0.0** → **1.1.0**: New features, backwards-compatible
- **1.0.0** → **2.0.0**: Breaking changes

### Tag Format
Always use `v` prefix: `v1.0.0`, `v1.1.0`, etc.

### Testing
Before tagging:
1. Test on macOS (if available)
2. Update all documentation
3. Run local build to verify
4. Check .env.example is current

### Release Notes
Make them useful:
- Highlight new features
- List breaking changes
- Include upgrade instructions
- Add screenshots for UI changes

## 🌟 Quick Commands

```bash
# Check current version
cat VERSION

# View recent tags
git tag -l | tail -5

# View workflow runs
gh run list --workflow=release.yml --limit 5

# Download release artifacts
gh release download v1.0.0

# Create pre-release
git tag v1.1.0-beta.1
git push origin v1.1.0-beta.1
```

## ✨ What's Automated

✅ Version extraction from VERSION file  
✅ Changelog extraction for release notes  
✅ Python environment setup  
✅ Dependency installation  
✅ Icon generation (Windows)  
✅ PyInstaller build  
✅ Archive creation  
✅ GitHub Release creation  
✅ Asset upload  
✅ Release publishing  

## 🎉 You're All Set!

Just update VERSION, commit, tag, and push. GitHub Actions does the rest!

```bash
# One command to release:
echo "1.1.0" > VERSION && \
git add VERSION CHANGELOG.md && \
git commit -m "Release v1.1.0" && \
git tag v1.1.0 && \
git push origin main v1.1.0
```

Then watch the magic happen at:
`https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
