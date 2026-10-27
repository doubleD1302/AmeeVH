# Launcher candidate r09

Isolated revision from launcher_next_r08. Adds a compact exclusive bank/MoMo payment row using exact QR crops supplied by the user; real auto-discovery instead of the visible path-copy button; unified GitHub repository/branch synchronization with explicit custom endpoints retained; four clearer guide sections and eleven FAQs. Keeps the left Việt Hoá mark, Nunito typography, resource packaging and installer/rollback safety.

Run from the project parent with `.venv/Scripts/python.exe -m launcher_next_r09.app`; build only with `.venv/Scripts/python.exe launcher_next_r09/build.py`. The delivered onefile candidate is under dist/launcher_ui_candidate_r09. These commands are documentation; the agent did not run the app.

Default online installation re-resolves the release, verifies the raw manifest asset digest, and installs only compatible declared files. Public v0.9.7 currently declares 63 image bundles; unlisted data/lua archives are never synthesized. Independent custom manifests must provide direct file URLs or an exact declared package filename/hash/size binding. Invalid repository configuration stays preserved, disables online operations with a clear message, and can be corrected in Settings; local game discovery remains available.

No application, Qt UI, EXE or tests were run. Initial independent source review found two issues; root corrected them after both subagents stopped for workspace credit exhaustion. Final independent review is pending. Build success is not runtime or installation proof. No GitHub publish/upload, bank transaction or game deployment is performed by this task.
