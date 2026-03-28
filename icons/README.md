# Genesis AI Systems Icon Documentation

This directory contains the required icons for the Progressive Web App (PWA) and platform integrations for Genesis AI Systems.

## Required Icon Sizes

To meet PWA and device requirements, you must generate:

- **192x192 px**  →  `icon-192.png`
- **512x512 px**  →  `icon-512.png`

Both must be PNG format, with a transparent background or the Genesis AI Systems brand navy (`#0f172a`), and contain the official logo using the Electric Blue (`#2563eb`) accent where appropriate.

These icons are referenced in the PWA `manifest.json` and used for:
- PWA install banners
- Home screen bookmarks on Android and iOS (Apple touch icon)
- Some browsers as favicons (192x192 as fallback)

## How to Generate Icons from the Genesis AI Systems Logo (SVG)

### 1. Obtain the Official Logo SVG
Use the official Genesis AI Systems logo in SVG format. The SVG must use:
- Brand Navy: `#0f172a` (background or main shape)
- Electric Blue: `#2563eb` (accents or details)
- Transparent background for maximum versatility.

### 2. Export the Required PNG Icon Sizes
You can use design software (Figma, Adobe Illustrator, Inkscape) or command line tools to create optimal icons.

#### *A. Using Figma, Illustrator, or Inkscape*
1. Open your SVG logo in your vector tool.
2. Set the canvas/artboard size to `192x192` or `512x512` px.
3. Center and scale the logo within the canvas, leaving margin to avoid cropping at rounded icon display.
4. Export as PNG:
    - Save `icon-192.png` at 192x192 px
    - Save `icon-512.png` at 512x512 px

#### *B. Using Inkscape from the Command Line*
```bash
inkscape logo.svg -o icon-192.png -w 192 -h 192
inkscape logo.svg -o icon-512.png -w 512 -h 512
```

#### *C. Using ImageMagick (for PNG source)*
If you have a transparent PNG source (not SVG):
```bash
convert logo.png -resize 192x192 icon-192.png
convert logo.png -resize 512x512 icon-512.png
```

### 3. Verify Icon Quality
- Preview each icon at its native size and on dark and light backgrounds.
- Make sure main logo elements are clearly visible and crisp at both sizes.
- Test on Android or Chrome by installing the PWA.

### 4. Replace or Update Icons
- Place both `icon-192.png` and `icon-512.png` in the `/icons/` directory.
- The paths are referenced by `/manifest.json` and in Apple Touch Icon meta tag—no renaming needed unless you update the logo design.

## Brand Colors Reference
- **Navy**: `#0f172a`
- **Electric Blue**: `#2563eb`

## Usage in PWA and Website
- `icon-192.png` and `icon-512.png` are specified in `manifest.json` for PWA installs
- `icon-192.png` is recommended for Apple touch splash and some browsers
- These icons help display the Genesis AI Systems logo on mobile home screens, install banners, and system app switchers

## Questions or Support
If you need help with icons or branding, contact:

Trendell Fordham  
Founder, Genesis AI Systems  
(313) 400-2575  
info@genesisai.systems
