# Context-py: Purpose and Overview

## Purpose

Context-py is a Python implementation of the babelfont file structure. Its primary purpose is to serve as the **code data model for a browser-based font editor**.

The package is specifically designed to support:

1. **Undo System** - Track and revert changes to font data structures
2. **Object Dirty Tracking** - Monitor which objects have been modified since the last save
3. **Browser-Based Editing** - Provide a clean data model that can be efficiently synchronized with a web-based UI

## Implementation Focus

While babelfont-rs (the Rust implementation) focuses on font format conversion and processing, context-py emphasizes:

- In-memory data manipulation
- Change tracking and history management
- Real-time editing support
- Serialization for web communication

## Babelfont Format References

For the canonical data structure definitions of the `.babelfont` format, refer to the babelfont-rs repository:

### Serde Serialization Definitions
The Rust struct definitions with `#[derive(Serialize, Deserialize)]` serve as the authoritative format specification:

- **Font structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/font.rs
- **Glyph structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/glyph.rs
- **Layer structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/layer.rs
- **Master structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/master.rs
- **Axis structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/axis.rs
- **Instance structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/instance.rs
- **Shape structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/shape.rs
- **Anchor structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/anchor.rs
- **Guide structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/guide.rs
- **Names structure**: https://github.com/simoncozens/babelfont-rs/blob/main/src/names.rs

### TypeScript Type Definitions
For TypeScript integration (useful for browser-based editors):

- **TypeScript generator example**: https://github.com/simoncozens/babelfont-rs/blob/main/examples/dump-typescript/main.rs
- The TypeScript definitions are generated using the `typescript-type-def` feature in Rust

## File Format Support

According to babelfont-rs:

- **`.babelfont`** - Single JSON file format (primary format for this package)
- **`.glyphspackage`** - Folder structure (Glyphs.app format)
- **`.glyphs`** - Single file (Glyphs.app format)
- **`.ufo`** - Folder structure (Unified Font Object)
- **`.designspace`** - XML file with UFO references

Context-py focuses on the `.babelfont` JSON format for efficient browser-based editing workflows.

## Architecture Notes

The Python implementation should maintain compatibility with the babelfont-rs data structures to enable:

- Round-trip conversion between formats
- Interoperability with Rust-based font tools
- Consistent data representation across platforms

## Development

When implementing new features or modifying data structures, always refer to the babelfont-rs Serde definitions as the source of truth for the `.babelfont` format specification.
