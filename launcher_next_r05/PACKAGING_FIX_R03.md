# r03 packaging correction

The user-observed r02 failure was `ImportError: DLL load failed while importing QtWidgets: The specified procedure could not be found`. Static import/export analysis found Qt6Core requires20 bare ICU C entrypoints, but r02 bundled an incompatible icuuc.dll from the Codex Poppler runtime through ambient PATH.

r03 leaves application behavior intact, changing the package namespace, build output and launcher caption only. The same candidate user-data directory is retained so settings/backup/journals are not discarded.

Build uses an allowlisted PATH containing the selected Python/venv, Qt wheel and Windows paths. PYTHONPATH, Qt/QML plugin overrides and Conda routing variables are removed only in the build subprocess environment. Neither the shared venv nor the user/system environment is modified.

The spec verifies by reading PE tables that Windows System32 icuuc.dll exposes Qt's required named entrypoints. It excludes bare system ICU names from the bundle, leaving the supported Windows ICU provider to the OS loader. No system or game DLL is copied. All collected binaries must originate under the selected Python/venv or Windows roots; dependency source/hash inventory is recorded.

No executable, Qt module, application or tests were run to validate this correction. Static packaging evidence does not prove runtime startup/UI success. The user will try the resulting candidate.

References:
- https://learn.microsoft.com/en-us/windows/win32/intl/international-components-for-unicode--icu-
- https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html
- https://doc.qt.io/qt-6/windows-deployment.html
- https://github.com/pyinstaller/pyinstaller/blob/develop/PyInstaller/depend/bindepend.py
