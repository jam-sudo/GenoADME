# `data/pharmgkb/`

PharmGKB / CPIC star-allele definitions for ADME genes (CC-BY licensed).

## Status

Empty in v0.1.0 skeleton.

## What goes here

- CPIC star-allele tables per gene (variant → allele label, allele → activity score, allele pair → phenotype label).
- A snapshot version stamp recording the PharmGKB release date and SHA so the preprint can pin to a specific table version.

## What does NOT go here

- Internally-modified versions of CPIC tables. If a star-allele definition is found to be wrong upstream, the fix goes to PharmGKB, not into a local override.

## Phenotype labels

The labels used here (PM / IM / EM / NM / UM / RM) are defined upstream in `sisyphus.predict.phenotype.PHENOTYPE_SCALES`. GenoADME does not redefine them. See [`../../docs/architecture.md`](../../docs/architecture.md) §1.

## License

PharmGKB allele definitions are CC-BY. CPIC guidelines are public. Both are redistributable with citation.
