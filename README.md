# testing

Prototypes for the Schulich pre-clerkship portal team to try out and give feedback on before anything reaches the live site ([schulichmed/preclerkship](https://github.com/schulichmed/preclerkship)).

Each prototype is a self-contained folder with an `index.html`. Open `index.html` at the root for the list.

| Prototype | What it asks |
|---|---|
| [`body-map/`](body-map/) | One 3D body (BodyParts3D skeleton, muscles and skin, CC BY 4.0) with five views: **Where it hurts** (tap a region: its own MSK charts first, then the cross-cutting ones, each opening in a pop-up), **Which structure** (tap a ligament, tendon, muscle or bursa: its chart opens with that diagnosis lit, via `charts/<chart>/#col=<id>`), **Anatomy tables** (every table muscle on the body; tap one for its row, hide it to see underneath; the skull opens the cranial nerves) and **Dermatome map** (the anatomy tables' Dermatomes tab, framed as it is there), **Dermatomes** (the skin cut by level from the skeleton under it, labelled on the body, ISNCSCI key points, a find-the-level quiz). `body-map/build_body.py` and `body-map/build_layers.py` rebuild the models |
| [`charts/`](charts/) | The PoM 2 interactive overview charts the body map opens (Look, Walk, Test); `#col=<id>` opens one with that diagnosis focused, `?embed=1` drops its header for the pop-up |
| [`fom-pom1/`](fom-pom1/) | 81 overview charts for the clinical lectures of FoM and PoM 1, drawn in the PoM 2 structure (content files in the preclerkship repo's `tools/pathways/src/`) and made interactive (Look, Walk, Test) by `fom-pom1/build.py` |
| [`anatomy-tables/`](anatomy-tables/) | One page of anatomy tabs in lecture order: Andy's cranial nerve and muscle tables (each clinical note on the muscle it is about; Test hides a column until tapped), a drawn cranial nerve map (where each nerve leaves the brain, the opening it leaves the skull by, what it supplies; click a nerve for its table row or an opening for what passes through; quiz on openings, sensory/motor/both, functions and naming), the dermatome map, and an interactive brachial plexus (click a part to light its path; quiz on roots, origins and what each nerve supplies). `anatomy-tables/build.py` rebuilds it from `vault_tables.json`, `plexus.html` and `template.html` |
| [`dermatomes/`](dermatomes/) | Shown as the Dermatomes tab of [`anatomy-tables/`](anatomy-tables/#dermatomes) (framed with `?embed=1`); still opens on its own. The JABSOM dermatome model from Sketchfab, embedded, with the C5 to C8/T1 and L2 to S1 table: click a level to fly to its test point, test yourself by naming or finding the point. Below it, a 3D spine (BodyParts3D bones, CC BY 4.0) with the cord and all 31 pairs of roots at their real exit levels, linked to the skin model; `dermatomes/build_spine.py` rebuilds it |
| [`pelvic-pain/`](pelvic-pain/) | The existing pelvic pain overview chart made interactive: focus a diagnosis, walk its questions, or hide a row to test yourself |
| [`pom2-note-visuals/`](pom2-note-visuals/) | Four ways (A to D) to work mnemonic tiles, numbers to know, tricky points and pearls into three PoM 2 notes, below the existing interactive chart |
| [`chart-merge/`](chart-merge/) | Five ways (A to E) to combine a lecture note's overview chart with the diagnostic flowcharts, on the thyroid example |

**Author:** nsimsam, with Claude Code. Built 2026-10-18.
