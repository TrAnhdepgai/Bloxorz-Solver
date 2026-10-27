**Số node mở rộng**

| Màn | Nhóm | BFS | DFS | IDS | UCS | ASTAR |
|---|---|---:|---:|---:|---:|---:|
| 01_basic_first_steps | basic | 4 | 36 | 3 | 4 | 2 |
| 04_basic_step_aside | basic | 31 | 43 | 38 | 34 | 19 |
| 06_basic_two_rooms | basic | 92 | 102 | 618 | 95 | 73 |
| 08_basic_courtyard | basic | 101 | 85 | 806 | 105 | 87 |
| 09_fragile_orange_crossing | fragile | 70 | 56 | 637 | 70 | 65 |
| 11_fragile_side_by_side | fragile | 84 | 69 | 1,096 | 81 | 54 |
| 13_fragile_fragile_yard | fragile | 224 | 167 | 1,765 | 225 | 77 |
| 14_switch_soft_touch | switch | 135 | 108 | 746 | 138 | 82 |
| 16_switch_heavy_step | switch | 181 | 130 | 1,734 | 177 | 106 |
| 17_switch_two_bridges | switch | 267 | 215 | 7,262 | 273 | 211 |
| 18_switch_lower_gate | switch | 186 | 198 | 4,724 | 194 | 136 |
| 19_split_split_lesson | switch | 2,336 | 183 | 26,903 | 2,605 | 2,324 |
| 21_split_rejoin | switch | 3,100 | 198 | 54,900 | 3,554 | 2,973 |
| 22_combined_glass_gate | combined | 141 | 109 | 3,049 | 142 | 116 |
| 24_combined_fragile_approach | combined | 187 | 182 | 2,596 | 183 | 132 |
| 26_combined_double_lock | combined | 310 | 307 | 16,902 | 327 | 255 |

**Thời gian tìm kiếm, ms**

| Màn | Nhóm | BFS | DFS | IDS | UCS | ASTAR |
|---|---|---:|---:|---:|---:|---:|
| 01_basic_first_steps | basic | 0.11 | 0.73 | 0.11 | 0.14 | 0.17 |
| 04_basic_step_aside | basic | 0.66 | 0.89 | 0.92 | 0.83 | 0.52 |
| 06_basic_two_rooms | basic | 1.86 | 3.14 | 14.42 | 2.10 | 1.91 |
| 08_basic_courtyard | basic | 1.80 | 1.57 | 17.76 | 2.34 | 2.11 |
| 09_fragile_orange_crossing | fragile | 1.72 | 1.08 | 14.15 | 1.53 | 1.61 |
| 11_fragile_side_by_side | fragile | 1.87 | 1.51 | 26.52 | 1.95 | 1.29 |
| 13_fragile_fragile_yard | fragile | 4.66 | 4.03 | 44.32 | 5.49 | 2.46 |
| 14_switch_soft_touch | switch | 2.75 | 2.31 | 17.98 | 3.34 | 2.21 |
| 16_switch_heavy_step | switch | 3.95 | 2.90 | 42.13 | 4.38 | 2.87 |
| 17_switch_two_bridges | switch | 5.36 | 4.64 | 169 | 8.13 | 5.92 |
| 18_switch_lower_gate | switch | 3.83 | 4.19 | 119 | 4.57 | 3.53 |
| 19_split_split_lesson | switch | 48.97 | 3.52 | 707 | 73.53 | 68.96 |
| 21_split_rejoin | switch | 80.57 | 4.62 | 1,492 | 108 | 94.57 |
| 22_combined_glass_gate | combined | 2.48 | 2.17 | 63.52 | 3.01 | 2.73 |
| 24_combined_fragile_approach | combined | 3.37 | 3.77 | 60.65 | 4.48 | 3.65 |
| 26_combined_double_lock | combined | 6.28 | 5.91 | 399 | 6.84 | 6.47 |

**Bộ nhớ đỉnh, KB**

| Màn | Nhóm | BFS | DFS | IDS | UCS | ASTAR |
|---|---|---:|---:|---:|---:|---:|
| 01_basic_first_steps | basic | 4.02 | 14.02 | 2.52 | 4.55 | 5.38 |
| 04_basic_step_aside | basic | 14.34 | 20.52 | 8.23 | 19.61 | 17.20 |
| 06_basic_two_rooms | basic | 30.06 | 41.77 | 24.01 | 37.35 | 40.18 |
| 08_basic_courtyard | basic | 30.52 | 32.27 | 24.55 | 37.78 | 42.12 |
| 09_fragile_orange_crossing | fragile | 17.73 | 22.80 | 18.96 | 22.31 | 26.81 |
| 11_fragile_side_by_side | fragile | 28.05 | 25.95 | 19.74 | 35.62 | 33.71 |
| 13_fragile_fragile_yard | fragile | 56.28 | 79.61 | 48.32 | 72.13 | 68.84 |
| 14_switch_soft_touch | switch | 39.21 | 50.81 | 32.67 | 47.77 | 46.12 |
| 16_switch_heavy_step | switch | 45.89 | 62.82 | 45.91 | 61.34 | 55.82 |
| 17_switch_two_bridges | switch | 62.03 | 97.68 | 64.77 | 79.48 | 80.52 |
| 18_switch_lower_gate | switch | 45.36 | 72.45 | 50.13 | 63.23 | 57.79 |
| 19_split_split_lesson | switch | 1,033 | 105 | 980 | 1,420 | 1,264 |
| 21_split_rejoin | switch | 1,350 | 115 | 1,349 | 1,786 | 1,636 |
| 22_combined_glass_gate | combined | 39.09 | 48.80 | 36.91 | 47.20 | 53.45 |
| 24_combined_fragile_approach | combined | 48.53 | 69.16 | 51.22 | 62.87 | 78.59 |
| 26_combined_double_lock | combined | 97.72 | 144 | 73.94 | 117 | 101 |

**Độ dài lời giải, số nước**

| Màn | Nhóm | BFS | DFS | IDS | UCS | ASTAR | Tối ưu |
|---|---|---:|---:|---:|---:|---:|---:|
| 01_basic_first_steps | basic | 2 | 2 | 2 | 2 | 2 | 2 |
| 04_basic_step_aside | basic | 5 | 40 | 5 | 6 | 6 | 5 |
| 06_basic_two_rooms | basic | 11 | 78 | 11 | 11 | 11 | 11 |
| 08_basic_courtyard | basic | 14 | 57 | 14 | 14 | 14 | 14 |
| 09_fragile_orange_crossing | fragile | 12 | 49 | 12 | 13 | 13 | 12 |
| 11_fragile_side_by_side | fragile | 13 | 58 | 13 | 13 | 13 | 13 |
| 13_fragile_fragile_yard | fragile | 11 | 150 | 11 | 13 | 13 | 11 |
| 14_switch_soft_touch | switch | 11 | 85 | 11 | 12 | 12 | 11 |
| 16_switch_heavy_step | switch | 14 | 111 | 14 | 16 | 16 | 14 |
| 17_switch_two_bridges | switch | 21 | 194 | 21 | 23 | 23 | 21 |
| 18_switch_lower_gate | switch | 20 | 124 | 20 | 20 | 20 | 20 |
| 19_split_split_lesson | switch | 16 | 106 | 16 | 16 | 18 | 16 |
| 21_split_rejoin | switch | 19 | 130 | 19 | 19 | 19 | 19 |
| 22_combined_glass_gate | combined | 16 | 81 | 16 | 17 | 17 | 16 |
| 24_combined_fragile_approach | combined | 15 | 109 | 15 | 15 | 15 | 15 |
| 26_combined_double_lock | combined | 27 | 204 | 27 | 29 | 29 | 27 |

**Chi phí lời giải**

| Màn | Nhóm | BFS | DFS | IDS | UCS | ASTAR | Nhỏ nhất |
|---|---|---:|---:|---:|---:|---:|---:|
| 01_basic_first_steps | basic | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 |
| 04_basic_step_aside | basic | 9.00 | 66.00 | 9.00 | 8.00 | 8.00 | 8.00 |
| 06_basic_two_rooms | basic | 19.00 | 130 | 19.00 | 19.00 | 19.00 | 19.00 |
| 08_basic_courtyard | basic | 26.00 | 93.00 | 26.00 | 26.00 | 26.00 | 26.00 |
| 09_fragile_orange_crossing | fragile | 20.00 | 79.00 | 20.00 | 19.00 | 19.00 | 19.00 |
| 11_fragile_side_by_side | fragile | 21.00 | 92.00 | 21.00 | 21.00 | 21.00 | 21.00 |
| 13_fragile_fragile_yard | fragile | 19.00 | 244 | 19.00 | 17.00 | 17.00 | 17.00 |
| 14_switch_soft_touch | switch | 19.00 | 135 | 19.00 | 18.00 | 18.00 | 18.00 |
| 16_switch_heavy_step | switch | 24.00 | 177 | 24.00 | 22.00 | 22.00 | 22.00 |
| 17_switch_two_bridges | switch | 37.00 | 308 | 37.00 | 35.00 | 35.00 | 35.00 |
| 18_switch_lower_gate | switch | 36.00 | 202 | 36.00 | 36.00 | 36.00 | 36.00 |
| 19_split_split_lesson | switch | 21.00 | 149 | 21.00 | 21.00 | 21.00 | 21.00 |
| 21_split_rejoin | switch | 26.00 | 185 | 26.00 | 24.00 | 24.00 | 24.00 |
| 22_combined_glass_gate | combined | 24.00 | 127 | 24.00 | 23.00 | 23.00 | 23.00 |
| 24_combined_fragile_approach | combined | 21.00 | 173 | 21.00 | 21.00 | 21.00 | 21.00 |
| 26_combined_double_lock | combined | 47.00 | 322 | 47.00 | 45.00 | 45.00 | 45.00 |
