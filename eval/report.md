# Search Evaluation Report

## Overall (macro over queries)

| mode | cases | P@5 | R@5 | F1@5 | nDCG@5 | P@10 | R@10 | F1@10 | nDCG@10 | MRR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| keyword | 28 | 0.543 | 0.170 | 0.214 | 0.562 | 0.514 | 0.309 | 0.306 | 0.570 | 0.633 |
| hybrid | 28 | 0.571 | 0.186 | 0.224 | 0.592 | 0.543 | 0.315 | 0.316 | 0.598 | 0.638 |
| oracle | 28 | 0.964 | 0.242 | 0.331 | 0.964 | 0.964 | 0.387 | 0.492 | 0.964 | 0.964 |

## Overall (micro, pooled counts)

| mode | cases | P@5 | R@5 | F1@5 | P@10 | R@10 | F1@10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| keyword | 28 | 0.543 | 0.076 | 0.133 | 0.514 | 0.144 | 0.225 |
| hybrid | 28 | 0.571 | 0.080 | 0.140 | 0.543 | 0.152 | 0.237 |
| oracle | 28 | 1.000 | 0.129 | 0.229 | 1.000 | 0.248 | 0.397 |

## By category (at k=5)

| category | mode | cases | P | R | F1 |
| --- | --- | --- | --- | --- | --- |
| structured | keyword | 18 | 0.556 | 0.074 | 0.131 |
| structured | hybrid | 18 | 0.589 | 0.079 | 0.139 |
| structured | oracle | 18 | 1.000 | 0.121 | 0.217 |
| semantic | keyword | 10 | 0.520 | 0.080 | 0.139 |
| semantic | hybrid | 10 | 0.540 | 0.083 | 0.144 |
| semantic | oracle | 10 | 1.000 | 0.145 | 0.253 |

## Negative queries (expected empty)

| mode | cases | returned_any | false_positive_rate |
| --- | --- | --- | --- |
| keyword | 5 | 5 | 1.000 |
| hybrid | 5 | 5 | 1.000 |
| oracle | 5 | 0 | 0.000 |

