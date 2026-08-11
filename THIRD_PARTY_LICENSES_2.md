# Third-Party Components and Licensing Notice

The MUIO codebase itself is licensed under Apache License 2.0 (see [LICENSE](./LICENSE)).
However, this repository includes or depends on certain third-party frontend
components that are **not** covered by the Apache-2.0 license and remain
subject to their own, separate license terms. This notice exists to make
that distinction clear to anyone using, forking, or redistributing this code.

---

## A. Components with restricted / commercial licenses

### 1. Wijmo (MESCIUS / GrapeCity)

- **Used for:** Displaying results on the Results form — specifically the
  OLAP-style results table (pivot table) and associated charting of model
  output data.
- **License type:** Commercial, per-developer license (Wijmo Enterprise / Commercial License Agreement)
- **Status:** A paid developer license has been purchased by the IAEA and
  registered under the developer's official IAEA email account.
- **What this covers:** The right of the license holder to develop and
  distribute compiled applications built with Wijmo.
- **What this does NOT cover:** Wijmo's commercial EULA does not grant a
  general right for third parties to reuse, further develop, or
  redistribute the Wijmo library itself. Under Wijmo's license terms,
  anyone wishing to further develop an application using these components
  is required to obtain their own developer license from MESCIUS
  (https://developer.mescius.com/wijmo/licensing).
- **Practical implication for downstream users:** You may run a built/compiled
  release of MUIO. If you intend to modify, rebuild, or redistribute the
  parts of MUIO that depend on Wijmo, you must obtain your own Wijmo license.

### 2. SmartAdmin (Webora / Wrapbootstrap)

- **Used for:** Dashboard layout and general UI theme/template for the
  WebAPP frontend.
- **License type:** Commercial template license (Wrapbootstrap / Wrapmarket)
- **Status:** ⚠️ Unresolved. The copy of SmartAdmin used in this project was
  obtained as a free template, not through a paid commercial license.
  According to the vendor's official licensing terms, SmartAdmin is sold
  exclusively through Wrapbootstrap/Wrapmarket, and copies found elsewhere
  are not authorized — "if you happen to find this item available on any
  other website, please report it... Yes you will need to pay to use
  SmartAdmin." A solution (proper licensing or replacement) is actively
  being sought.
- **What this means:** SmartAdmin is sold exclusively through Wrapbootstrap/
  Wrapmarket. Its license terms explicitly prohibit public redistribution
  of the source template, even under a paid license, without an Extended
  License and code obfuscation. Use of an unlicensed copy, and its inclusion
  in a public Apache-2.0 repository, is **not currently compliant** with
  SmartAdmin's license terms.
- **Action required:** This dependency needs to be either (a) properly
  licensed and then handled per the Extended License requirements, or
  (b) replaced entirely with an open-source alternative.

### 3. jQWidgets

- **Used for:** Grid components used throughout the application, as well as
  various other UI elements (e.g. input controls, layout/navigation widgets).
- **License type:** Commercial (jQWidgets license)
- **Status:** A paid license has been purchased by the IAEA and registered
  under the developer's official IAEA email account.
- **What this covers / does not cover:** [same structure as above — confirm
  whether the jQWidgets license terms permit redistribution of the library
  itself as part of a publicly redistributable Apache-2.0 codebase, or
  whether they are limited to the license holder's own development and
  distribution of compiled applications, as with Wijmo above]

---

## B. Components with permissive open-source licenses

The following third-party libraries used in MUIO are fully open-source and
impose no restrictions on redistribution, modification, or commercial use
beyond retaining their copyright/license notice, as required by the MIT
License:

| Library | License | Source |
|---|---|---|
| [json-logic-js](https://github.com/jwadhams/json-logic-js) | MIT | github.com/jwadhams/json-logic-js |
| [Mermaid.js](https://github.com/mermaid-js/mermaid) | MIT | github.com/mermaid-js/mermaid |
| [Plotly.js](https://github.com/plotly/plotly.js) | MIT | github.com/plotly/plotly.js |
| [crossroads.js](https://github.com/millermedeiros/crossroads.js) | MIT | github.com/millermedeiros/crossroads.js |

These components require no license purchase, place no restriction on
downstream use (academic, institutional, government, NGO, or commercial),
and are compatible with the Apache-2.0 license under which the MUIO
codebase itself is distributed.

---

## Summary for downstream users

- The MUIO-original code (Python/API, and original JS/CSS authored for this
  project), together with the open-source components listed in Section B,
  are freely usable, modifiable, and redistributable, including for
  commercial, government, NGO, or institutional purposes.
- The third-party UI components listed in Section A are **not** Apache-2.0
  and are **not** free to redistribute or further develop without your own
  license from the respective vendor (or, in the case of SmartAdmin, without
  first resolving the licensing issue described above).
- Downstream users planning to build on or redistribute MUIO should treat
  the Section A components as a separate licensing obligation, independent
  of the Apache-2.0 license covering the rest of the repository.
