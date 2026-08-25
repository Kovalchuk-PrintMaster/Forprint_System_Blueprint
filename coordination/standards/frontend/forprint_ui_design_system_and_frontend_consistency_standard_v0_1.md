# ForPrint UI Design System and Frontend Consistency Standard v0.1

## Status

Mandatory frontend/UI governance standard for any ForPrint work that creates or changes a
human-facing web interface.

Any execution prompt that modifies frontend/UI MUST include this standard or its current successor in
authoritative context.

## Core law

**A page MUST NOT invent its own visual language.**

Pages compose approved design tokens, layout primitives and reusable UI components.

The target architecture is:

`Design Tokens → UI Primitives → Reusable Components → Page Composition`

A page-specific workaround is not a design system.

## Required design-token ownership

Colors, typography, spacing, radius, shadows, motion, z-index and breakpoints MUST come from a shared
token system or explicit approved extension.

Forbidden in normal page/component code:

- arbitrary raw HEX/RGB/HSL colors when a semantic token should exist;
- arbitrary font families;
- arbitrary spacing/radius/shadow values that duplicate design-system concepts;
- page-local semantic colors such as one-off warning red/orange;
- visually equivalent values redefined under different names.

Semantic tokens SHOULD express purpose, for example:

- `--fp-color-warning`
- `--fp-color-danger`
- `--fp-color-success`
- `--fp-font-heading`
- `--fp-font-body`
- `--fp-space-md`
- `--fp-radius-control`
- `--fp-shadow-panel`
- `--fp-duration-fast`

If warning color changes centrally, all compliant warning UI should change without editing every page.

## Shared component requirement

Common UI must be reusable components/primitives, for example:

- Button
- Input
- Select
- Checkbox
- Badge
- Card
- Panel
- Dialog
- Table
- Tabs
- Tooltip
- Toast
- Dropdown
- Navigation
- FormRow

Pages MUST reuse approved components before creating new ones.

If a genuinely new reusable pattern is needed, add it once to the component system with documented
purpose/states/variants rather than implementing a private page-local version.

## Component registry

The design system SHOULD maintain stable component identities and documentation covering:

- purpose;
- variants;
- states;
- allowed use;
- accessibility behaviour;
- examples;
- deprecated variants.

## Cascade and specificity law

The following are prohibited as normal conflict-resolution techniques:

- `!important`;
- escalating selector specificity to "win";
- copy/paste CSS overrides across pages;
- broad global selectors that leak into unrelated components;
- page-specific rules that restyle shared components;
- inline style attributes used as a styling architecture.

Exceptions require explicit rationale and should be temporary, tracked debt.

Recommended CSS architecture includes:

- CSS Custom Properties;
- semantic design tokens;
- low-specificity selectors;
- scoped component styles;
- cascade layers such as `reset, tokens, base, components, utilities, pages`.

## Page CSS boundary

Page-specific CSS SHOULD primarily control composition:

- grid/column arrangement;
- page regions;
- responsive placement;
- sticky/fixed layout relationships.

It SHOULD NOT redefine the visual identity of shared controls.

## UI quality target

Consistency does not mean a gray/static interface.

ForPrint UI SHOULD be modern, responsive, polished and interactive, with justified use of:

- transitions and microanimations;
- hover/focus states;
- drawers/modals;
- contextual shadows;
- progressive disclosure;
- skeleton/loading states;
- rich tables/charts;
- drag/drop where useful;
- responsive layouts.

Effects must still come from approved motion/visual primitives rather than one-off page inventions.

## Theme model

Theme is an independent appearance axis.

Mandatory:

- `LIGHT`
- `DARK`

Optional decorative overlays may be introduced for:

- New Year;
- Easter;
- corporate events;
- other approved seasonal occasions.

Seasonal overlays MUST NOT redefine business semantics or accessibility behaviour. They may adjust
decorative headers, logo treatment, illustrations and approved surface accents.

A festive theme must not change what warning/success/danger means.

Future `HIGH_CONTRAST` support SHOULD remain architecturally possible even if not implemented in the
first release.

## Interface scale / density model

The UI MUST support at least three presets:

- `COMPACT`
- `STANDARD`
- `LARGE`

These are independent from LIGHT/DARK.

Examples:

- `DARK + COMPACT`
- `LIGHT + LARGE`

### Compact

Designed for small screens or users who prefer information density.

It may reduce:

- spacing;
- table row height;
- secondary chrome;
- nonessential whitespace.

It must not make text or click targets unreasonably small.

### Standard

Default balanced preset.

### Large

Accessibility-oriented preset for users who need larger text/controls.

It SHOULD increase:

- typography;
- controls;
- icons;
- click/touch targets;
- spacing where required for usability.

Layouts MUST reflow rather than simply overflow.

## Relative sizing

Typography and scalable UI SHOULD use relative units/design tokens so:

- user presets work consistently;
- normal browser zoom remains usable;
- pages reflow instead of breaking.

Application-level `LARGE` mode does not replace browser/OS accessibility.

## Preference persistence

User theme/scale choices SHOULD persist between sessions.

On first use, system LIGHT/DARK preference may be used as a default.
A user's explicit choice has higher priority.

## Minimum component states

Interactive components must account for appropriate states.

Button examples:

- default
- hover
- focus
- active
- disabled
- loading

Input examples:

- default
- focus
- filled
- invalid
- disabled
- readonly

Pages/components must also consider:

- loading;
- empty;
- error;
- permission-denied;
- partial-data conditions where relevant.

## Accessibility

UI work MUST consider:

- keyboard navigation;
- visible focus;
- semantic HTML;
- labels and form semantics;
- contrast;
- screen-reader compatibility;
- responsive reflow;
- meaningful error/validation states.

WCAG-aligned implementation is the default direction.

## Health test

If changing one design decision requires manually editing many pages, the frontend architecture is
likely wrong.

A compliant system normally changes:

- a token; or
- a shared component;

and lets dependent pages update automatically.

## Frontend debt rule

"Make it locally now and unify later" is not an acceptable default strategy.

A new visual pattern either:

1. belongs in the shared design system immediately; or
2. remains an explicitly approved experiment/exception.

Frontend inconsistency is not postponed until ten pages have already diverged.
