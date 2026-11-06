---
name: reference-to-live2d
description: Build or revise an illustrated Live2D character from reference art through measured proportions, coherent head artwork, natural-pose body artwork, rig assembly, seam and blink repair, and runtime review. Use for reference-driven modeling and correcting identity, shoulder-pose or facial seams, not unrelated image generation or ChatGPT Pets.
---

# Reference to Live2D

Produce a character that retains its approved appearance and looks natural in its resting pose. Compare the actual face, shoulder anatomy, fabric folds and moving seams; a renderable model is not enough.

## Start from the current stage

Inspect repository instructions, approved artwork, measurements, editable models and runtime entrypoints. Continue from existing approved work instead of regenerating every stage.

- Read [workflow.md](references/workflow.md) for production decisions and measurement conventions.
- For facial patches, motion cracks or broken blinks, read [seam-repair.md](references/seam-repair.md); start from the existing model rather than repeating reference generation.
- Before generating artwork, read the relevant template in [prompts.md](references/prompts.md). Use the available image-generation skill/tool for raster work and preserve generated alpha.
- In `TraitYoung/alive-bina`, read [bina-repository.md](references/bina-repository.md) for paths, commands and accepted/rejected artifacts. Do not apply Bina's coordinates or character design to another project.

## Workflow

1. **Approve T-pose references.** Establish consistent identity, outfit and proportions across front/back/side. Save sources, dimensions, hashes and actual prompts when available.
2. **Measure originals.** Mark visible landmarks; leave obscured points null. Calculate proportions from actual marks, not target coordinates supplied to a generator. `scripts/measure_landmarks.py` accepts compatible landmark manifests; new drawings require newly reviewed marks.
3. **Resolve the whole head.** Generate a coherent head candidate when a redraw is needed. Review identity before splitting features. If the original face is already approved, retain its pixels and generate masks/hidden underpainting as needed. Label rejected candidates.
4. **Generate the resting body.** Use T-pose as a design/proportion reference and redraw shoulders, armholes, gravity-driven folds, relaxed elbows and hands for the target pose. Rotating T-pose sleeves is not a substitute for natural standing artwork in this workflow.
5. **Assemble approved sources.** Keep facial features registered to one coherent source. Register the new body to the approved head/neck with uniform scaling and translation. Remove the generated head when retaining the original; inspect neck seams at rest and during motion.
6. **Rig and export.** Use the native editor's current tool schemas. Save editable sources; inspect masks, draw order, physics and export references. Distinguish a continuous body mesh from independently rigged limbs.
7. **Review the runtime.** Check neutral pose, idle, available motions/expressions, refresh, model selection and desktop/mobile display. Capture actual screenshots, resource failures and page errors.
8. **Repair demonstrated head failures.** Compare source artwork, neutral render and posed close-ups. Add outfit-specific hidden skin and neck overlap, peel soft feature layers, coordinate the head deformation chains and author the blink transition. Repeat close-up review before replacing runtime assets; see [seam-repair.md](references/seam-repair.md).
9. **Restore independent controls deliberately.** A continuous head can remove cracks while reducing hair or iris freedom. Restore separate hair physics, iris tracking and mouth controls only after preparing their hidden artwork and verifying combinations; report the current capabilities explicitly.

## Decisions that matter

- Measurements constrain generation; they do not make an unrecognizable face acceptable.
- Do not independently generate eyes, nose, mouth and hair and force them onto target coordinates. Split one approved coherent head in place.
- Label redraws, crops, interpolation and measurements accurately. Enlarging a source does not create original detail.
- Estimated shoulder joints under loose clothes are not the visible cardigan edges. Redraw anatomy and cloth together for a changed pose.
- Independent gestures require separate limb layers, overlap underpainting and controls. A continuous generated body can satisfy a standing/idle milestone; state its actual capability.
- Static pixel reconstruction and successful playback are separate from dynamic seam quality. Do not use an engine migration or increasingly severe runtime clamps as a substitute for repairing source art and deformation.
- Keep edits within the requested character and stage. This skill does not authorize pushing, publishing or changing other character runtimes.

## Deliverables

Save selected artwork, actual prompts, measurement inputs/results, assembly metadata, editable models, runtime assets and verification evidence in the project. Report the model/preview location and material unfinished capabilities. Do not leave project assets only in a generator's private output directory.
