[README.md](https://github.com/user-attachments/files/31664017/README.md)
# p6-kontrol-paneli# Construction Planning & Control

A free dashboard for Primavera P6 schedules. Upload an `.xer` export and get the
earned value picture, critical path view, lookahead and a DCMA 14-point quality
check in one pass. No install, no account, nothing stored.

**Live app:** _add your Streamlit URL here_

![Overview tab](docs/overview.png)

## What it gives you

| Tab | Contents |
|---|---|
| Overview | SPI, CPI, EAC, VAC, TCPI, earned schedule, S-curve, progress by WBS |
| Schedule | P6-style Gantt with baseline bars and logic lines, lookahead, milestones, late activities |
| Critical Path | Float distribution, negative float, critical work by package |
| Earned Value | EVM table by WBS, SPI/CPI performance matrix, largest variances |
| Resources | Weekly or monthly histogram with cumulative curve, resource breakdown |
| Schedule Quality | DCMA 14-point check with a fix list |
| Baseline | Activity-level date and scope comparison between two `.xer` files |
| Data | Full activity table and multi-sheet Excel export |

Notes on the calculations:

- **Weighting** follows what the schedule actually carries — cost if it is cost
  loaded, quantities if it is resource loaded, otherwise duration as a weight.
  The unit in use is printed at the top of the Overview tab.
- **Progress** respects the P6 percent-complete type per activity (physical,
  units or duration) rather than assuming one of them.
- **Lookahead** filters on remaining early dates (`restart_date` / `reend_date`),
  which is what P6 itself uses, so in-progress work stays on the list until its
  remaining duration is consumed.
- **S-curves** are time-phased: each activity's budget is spread across its dates
  rather than accumulated at its finish.

## Run it locally

```bash
git clone <this-repo> && cd <this-repo>
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 and upload a file. `sample.xer` in the repo is
synthetic test data if you want to try it before using a real schedule.

## Deploy your own copy

See [DEPLOY.md](DEPLOY.md). The short version: push this folder to GitHub, point
Streamlit Community Cloud at `app.py`, done. Every setting in
`.streamlit/secrets.toml.example` is optional — the app runs with none of them.

## Privacy

Uploaded files are parsed in memory to draw the dashboard. They are never written
to disk, never sent onward and never shared between sessions. No schedule content
is logged and no usage analytics are collected. The Privacy panel inside the app
states this to your visitors, and a **Clear my data** button drops the session on
demand.

If you are handling commercially sensitive programmes, read the deployment table
in DEPLOY.md before putting them on a hosted service.

## Contributing

Issues and pull requests are welcome. Useful things to report:

- An `.xer` that fails to parse (please describe the P6 version and the export
  options rather than attaching a real schedule).
- A calculation that disagrees with P6, with the figures from both sides.
- Fields your organisation relies on that the dashboard ignores.

## Licence

MIT. See [LICENSE](LICENSE).

Not affiliated with or endorsed by Oracle. Primavera and P6 are trademarks of
Oracle Corporation. This tool only reads the exported file format.
