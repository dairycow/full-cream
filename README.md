# Full Cream

A collection of financial market related tools.

## Repository Structure

```
full-cream/
├── aus-ep-scan/              # Australian equity price scanning
│   ├── tv_scan.sh           # TradingView momentum scanner
│   ├── asx_ann_scan.sh      # ASX announcements scanner
│   ├── find_intersection.sh # Intersection analysis and GitHub summary
│   └── README.md            # Module documentation
├── .github/workflows/
│   └── aus-ep-scan.yml      # Automated scanning workflow
└── README.md                # This file
```

## Current Modules

### `aus-ep-scan/`
Australian equity scanning that combines TradingView scanner data with ASX price-sensitive announcements.

**Features:**
- Automated scans
- GitHub Actions workflow alerts
- Minimal dependencies

See [aus-ep-scan/README.md](aus-ep-scan/README.md) for detailed usage.

## Getting started
Each module contains its own README with specific usage instructions.
