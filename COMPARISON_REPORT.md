# השוואת פלטים: הפרויקט המקומי מול `ASG1_OOP`

> **Historical report — superseded by the 2026-11-02 validation fix.**
> These measurements describe the earlier permissive implementation. The
> current code rejects unequal legs, so this four-row input is not a valid
> current demo. Identical CSV bytes also did NOT mean identical trapezoid
> geometry: this project used `(a1,a2,b,c)`, while the compared project
> reordered `(a1,b,a2,c)`. Aggregate means/ranges do not establish visual
> similarity or pixel equivalence. Treat the measurements below as historical
> observations, not proof of algorithm correctness. Current verification is
> documented in [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md).

## מטרת הבדיקה

להריץ את שני המימושים על אותו קלט ולבדוק אם ההיטל של המישור התלת־ממדי דומה.

## קלט וסביבת הרצה

- קובץ NRRD: `ASG1_OOP/DATA/MRHead_1.nrrd`
- קובץ מישורים: `ASG1_OOP/DATA/lecturer_example.csv`
- נפח: `256 x 256 x 130`, מסוג `int16`, טווח ערכים `0..279`
- Python: `3.13.14`
- שני הפרויקטים הורצו עם אותו קובץ NRRD ואותו CSV.

פקודות ההרצה:

```text
python Ex0.py DATA/MRHead_1.nrrd DATA/lecturer_example.csv comparison_github.mp4
python Ex0.py DATA/MRHead_1.nrrd DATA/lecturer_example.csv comparison_local.mp4
```

## תוצאות CLI

| פרויקט | סטטוס | מספר פריימים | הערות |
|---|---:|---:|---|
| מקומי | הצלחה | 4 | נוצר `comparison_local.mp4` |
| GitHub (`aviya1221/ASG1_OOP`) | הצלחה | 4 | נוצר `comparison_github.mp4`; פריים 3 קיבל אזהרה על רגליים באורכים שונים |

## השוואת ההיטל הגולמי לפני קידוד הווידאו

הנתונים הבאים נלקחו ישירות מהאלגוריתם, לפני דחיסת MP4. לכל פריים מוצגים `(גובה, רוחב)` ולאחריהם `(min, max, ממוצע, מספר פיקסלים שאינם אפס)`.

| פריים | מקומי | GitHub |
|---:|---|---|
| 1 | `(448, 401)`; `(0, 128, 2.40, 8,888)` | `(401, 401)`; `(0, 128, 2.39, 7,926)` |
| 2 | `(401, 501)`; `(0, 175, 7.04, 32,592)` | `(501, 401)`; `(0, 175, 7.04, 32,592)` |
| 3 | `(498, 454)`; `(0, 124, 2.56, 13,636)` | `(431, 453)`; `(0, 129, 2.55, 11,806)` |
| 4 | `(401, 503)`; `(0, 175, 8.71, 34,819)` | `(501, 401)`; `(0, 175, 6.85, 27,272)` |

## מסקנה

התשובה היא: **דומה חלקית, אך לא זהה**.

- שני המימושים מעבדים את אותו קלט ומחזירים 4 פריימים.
- בשלושה מתוך ארבעת הפריימים טווחי הערכים והממוצעים קרובים מאוד, ולכן נראה ששניהם דוגמים אזורים דומים בנפח.
- ממדי ההיטל שונים באופן מהותי, ובפריים 2 אף מתחלפים גובה ורוחב (`401 x 501` לעומת `501 x 401`).
- בפריים 4 גם הממוצע ומספר הפיקסלים שאינם אפס שונים בצורה בולטת.

לכן אי־אפשר לקבוע שהאלגוריתם המקומי מחזיר את אותה תוצאה כמו `ASG1_OOP`. הוא מחזיר תוצאה באותו סדר גודל ובדמיון חזותי חלקי, אבל קיימים הבדלים גאומטריים משמעותיים בממד, בכיוון הפריים ובאופן הדגימה.

הבדלים אלה מתאימים לכך שהמימושים משתמשים בהגדרות שונות לגודל התמונה ולריסטרוזציה של המישור: המימוש המקומי משתמש באינטרפולציה ישירה לאורך שתי צלעות, ואילו `ASG1_OOP` בונה מערכת צירים מקומית למישור ומחשב טווחי שורות/עמודות.

## קבצי הפלט

- `comparison_local.mp4` — פלט הפרויקט המקומי.
- `comparison_github.mp4` — פלט `ASG1_OOP`.

ההשוואה המספרית נעשתה על מערכי ההיטל לפני MP4, משום ש־H.264 הוא קידוד lossy ולכן אינו מתאים להשוואת פיקסלים מדויקת.
