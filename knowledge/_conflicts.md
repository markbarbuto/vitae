# Resume vs website conflicts

Report only. Not indexed.

Sources compared:

- Resume: `C:\Users\markb\Documents\Resume\ResumeMarkBarbuto.pdf` (Sep 23, newest)
- Website: `C:\Users\markb\projects\portfolio\src\data\` (`profile.ts`, `experience.ts`, `projects.ts`)

Rule: the resume wins. All direct contradictions were resolved on 2026-10-31.

## Vitae AI staleness

- Vitae AI is described on both the resume and the site as llama.cpp hosted on Oracle Cloud. Oracle A1 is now the chosen host, so both are accurate. The site card's year (2025) will be wrong if the build lands in 2026.
- Facts about the assistant itself come from the generated `self.md` (PLAN.md section 5, "Self-description"). The site card and resume are kept accurate by hand, with no CI check.

## Not compared

- `src/data/fun/*` (travel, Arsenal, music) and `skills.ts` icon groups have no resume counterpart.
- The older resumes in `Documents/Resume/Old/`.
