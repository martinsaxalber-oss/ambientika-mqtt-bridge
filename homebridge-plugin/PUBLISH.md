# Publishing homebridge-ambientika to npm

This guide describes the steps to publish the `homebridge-ambientika` plugin
to the npm registry so users can install it via:

```bash
npm install -g homebridge-ambientika
```

---

## Prerequisites

- Node.js 18+ installed
- An npm account at [npmjs.com](https://www.npmjs.com)
- 2FA enabled on npm account (required for public packages)

---

## Step 1: Create npm Account (if not yet done)

1. Go to [npmjs.com/signup](https://www.npmjs.com/signup)
2. Create account with your email
3. Enable 2FA in account settings (mandatory for publishing)

---

## Step 2: Clone and Prepare

```bash
git clone https://github.com/martinsaxalber-oss/ambientika-mqtt-bridge.git
cd ambientika-mqtt-bridge/homebridge-plugin
npm install
```

---

## Step 3: Login to npm

```bash
npm login
# Enter your npm username, password, email
# Complete 2FA if prompted
```

---

## Step 4: Verify package before publishing

```bash
# Dry run – shows what would be published without actually publishing
npm publish --dry-run

# Check the output – you should see these files:
# src/index.js
# package.json
# README.md
```

---

## Step 5: Publish

```bash
npm publish --access public
```

The plugin will be available at:
`https://www.npmjs.com/package/homebridge-ambientika`

---

## Step 6: Verify on Homebridge Plugin Repository

After publishing to npm, submit the plugin to the verified Homebridge plugin list:

1. Open [github.com/homebridge/homebridge/wiki/Verified-Plugins](https://github.com/homebridge/homebridge/wiki/Verified-Plugins)
2. Follow the verification checklist
3. Open a PR to add `homebridge-ambientika` to the verified list

**Verification requirements:**
- Plugin must be published on npm ✅ (after Step 5)
- `homebridge-plugin` keyword in package.json ✅
- Valid README with install instructions ✅
- Uses `homebridge` peerDependency ✅
- GitHub repo is public ✅

---

## Step 7: Update Version for Future Releases

```bash
# Bump version (patch = bug fix, minor = new feature, major = breaking change)
npm version patch   # e.g. 1.0.0 → 1.0.1
npm version minor   # e.g. 1.0.1 → 1.1.0
npm version major   # e.g. 1.1.0 → 2.0.0

# Publish new version
npm publish --access public

# Push version tag to GitHub
git push && git push --tags
```

---

## Notes

- The npm package name `homebridge-ambientika` must be unique on npmjs.com.
  Check availability at: `https://www.npmjs.com/package/homebridge-ambientika`
- If the name is taken, use `homebridge-ambientika-mqtt` as fallback
- Package scope (e.g. `@ambientika/homebridge-ambientika`) requires a paid npm org account
