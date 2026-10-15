# Town Department Headcount, FY2021-FY2027 (Annual Series)

Source: `data/FY2025-Financial-Plan.pdf` p.57, `data/FY2026-Financial-Plan.pdf` p.56, `data/FY2027-Financial-Plan.pdf` p.79-80 - each plan's own "Full-Time Equivalent Positions Funded" table (All Positions: General Fund + Capital/Special Appropriations + Grants + Enterprise/Revolving combined). Added 2026-09-02 (Ben: "yes please check the financial plan pdfs to see if they contain more department detail") - a real annual FY2021-2027 series, not just the FY2019/FY2026 two-point comparison in `department_fte_history.py`.

**Cross-validated, not assumed**: every department/year covered by more than one plan was checked directly. Full agreement for FY2021-2024. One real, traceable discrepancy for FY2025 (the FY2025 Plan's own recommended-year figure, 726.56 total, vs. 721.56 in the two later plans' settled figures - a real -5.00 FTE difference, traced to exactly 4 departments: Library, Public Works, Police, and ODEICR) - this file uses the later, settled figures; the FY2025 Plan's original recommended figures are kept in `fy2025_as_recommended_fy25plan` for comparison.

## Annual FTE by department (All Positions)

| Department | FY2021 | FY2022 | FY2023 | FY2024 | FY2025 | FY2026 | FY2027 | CAGR FY21-27 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Select Board | 7.00 | 7.00 | 8.50 | 8.00 | 10.00 | 10.00 | 9.00 | +4.28% |
| Human Resources | 6.78 | 6.78 | 6.78 | 6.78 | 6.78 | 7.78 | 6.78 | +0.00% |
| Information Technology | 12.40 | 12.40 | 12.00 | 12.00 | 13.00 | 13.00 | 13.00 | +0.79% |
| Finance Department | 31.22 | 31.22 | 31.92 | 31.92 | 29.42 | 29.42 | 27.00 | -2.39% |
| Legal Services | 7.71 | 7.71 | 7.71 | 7.71 | 8.71 | 8.21 | 8.21 | +1.05% |
| Advisory Committee | 0.40 | 0.40 | 0.40 | 0.40 | 0.40 | 0.40 | 0.40 | +0.00% |
| Town Clerk | 5.50 | 5.50 | 5.50 | 5.50 | 5.50 | 5.50 | 5.50 | +0.00% |
| Planning | 18.00 | 18.00 | 19.00 | 20.00 | 19.00 | 19.00 | 16.00 | -1.94% |
| Police | 179.80 | 179.80 | 179.80 | 175.80 | 173.30 | 172.30 | 171.10 | -0.82% |
| Fire | 161.00 | 161.00 | 161.00 | 161.00 | 161.00 | 161.00 | 160.00 | -0.10% |
| Building | 37.61 | 38.61 | 38.61 | 38.61 | 38.61 | 38.61 | 40.61 | +1.29% |
| Public Works | 130.91 | 131.91 | 131.91 | 134.91 | 139.91 | 133.91 | 132.92 | +0.25% |
| Recreation | 10.00 | 10.00 | 11.00 | 11.00 | 11.00 | 11.00 | 10.00 | +0.00% |
| DEICR | 3.72 | 3.72 | 3.72 | 2.72 | 3.72 | 3.72 | 3.72 | +0.00% |
| Health | 21.59 | 21.59 | 20.06 | 22.28 | 24.28 | 26.28 | 26.48 | +3.46% |
| Veterans' Services | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | 2.00 | +0.00% |
| Council on Aging | 17.40 | 18.01 | 18.01 | 18.01 | 18.71 | 19.09 | 19.09 | +1.56% |
| Library | 52.84 | 52.84 | 54.12 | 55.89 | 56.22 | 56.22 | 55.66 | +0.87% |

## What this deliberately does not do

- **FY2027 is the Town's own recommended budget, not yet an audited actual** - same caveat as every other "Town's own published" figure elsewhere in this project.
- **Doesn't reach back before FY2021** - `department_fte_history.py`'s ERSC-sourced FY2019 point is the only source in this project reaching that far back; the two datasets aren't directly merged since ERSC's FY2019/FY2026 salary figures and this file's annual FTE-only figures come from different sources with different exact scopes.
