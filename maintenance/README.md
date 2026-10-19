# Automated upstream watch

[Open Upstream watch in GitHub Actions](https://github.com/librerob/adwaita-amoled/actions/workflows/upstream-watch.yml).

The workflow runs on the first of each month, at 09:17 UK winter time / 10:17 UK
summer time (GitHub cron uses 09:17 UTC). GitHub may delay scheduled runs.
For an immediate check, open that page, choose **Run workflow**, select `main`
and confirm **Run workflow**. No personal token or additional secret is needed.

Open the completed run's **Summary** for its component table and upstream
comparison/source links. Download **upstream-review-report** under Artifacts
for Markdown and JSON copies; reports are retained for 90 days. New versions
appear as **review-needed** and workflow warnings. Finding an update is a
successful check, not a failing theme test. This does not send custom email,
create issues, or guarantee a notification; check the Actions report to review
updates. API/configuration failures fail the workflow and must not be read as
“up to date.” GitHub's own failure notifications depend on account preferences.

## What it checks

The catalog tracks GTK3, current/future GTK majors, libadwaita, GNOME desktop
release manifests, current/future GNOME Shell majors, the supported Shell 46
maintenance series, Cinnamon, Muffin, Xfce panel, Xfwm4 integration, MATE desktop,
Marco and Budgie. It uses the projects' public upstream GitHub repositories or
mirrors. Primary GitLab releases may reach a mirror later.

Baseline versions come from [the compatibility review](../COMPATIBILITY.md)
and the pinned Shell metadata. A baseline records the last review point; it
is not a claim that every desktop session or future point release is tested.
The MATE desktop baseline is the beginning of the reviewed 1.28 series;
Marco has its separate, specifically tested version.

All tag pages are considered, rather than trusting the first page or lexical
ordering. Numeric version comparison avoids mistakes such as ordering `.9`
after `.10`. Prerelease suffixes and build/branch tags are excluded. GTK,
libadwaita, Cinnamon/Muffin, Xfce and MATE/Marco use explicitly configured even
minor series; Budgie and modern GNOME Shell do not. Minor versions 90 and above
are excluded as development versions. These are conservative **tag rules**,
not a substitute for reading official release announcements. A project changing
its release scheme may require updating the rules. Pinned Shell tag commit
changes are flagged, and missing baseline tags or incomplete pagination produce
errors rather than a green “no-new-tag” result.

## Reviewing an update

1. Follow the comparison and source links. Read NEWS/release notes and changes
   to the relevant styles, widget nodes, assets, settings schemas or decorations.
2. Run the affected checks listed in the report and [tests guide](../tests/README.md)
   against the new dependency version. For a new desktop major, add native/session
   coverage before declaring it supported. Existing Ubuntu test images do not
   automatically upgrade to every new upstream release.
3. Reproduce suspected regressions before fixing them; rerun affected tests after
   a fix. A release can need review without requiring any theme modification.
4. Record versions, evidence and limits in `COMPATIBILITY.md`. Then update the
   relevant `baseline_tag` in `upstream-watch.json`; if it has a pinned
   `baseline_commit`, update that review commit too. Do not advance baselines
   just to clear warnings. The watch never edits upstream imports or baselines.

The workflow also runs when its code/configuration changes, so it can be tested
before merging. It is read-only and does not change colors, installer behavior,
release assets, tags or icon inheritance. Its files are not added to the
installer runtime payload. No new theme release is needed just for this watch.

For local development, Python 3.11+ and authenticated GitHub CLI are needed:

```bash
python3 tests/test_upstream_watch.py
python3 tools/upstream_watch.py --output /tmp/adwaita-upstream-report
```

GitHub can disable scheduled workflows on inactive public repositories after
60 days. If reports stop appearing, check the Actions page for a re-enable
banner. The watch does not detect unreleased branch changes, distribution-only
patches, arbitrary application CSS or hardware-specific rendering problems.
