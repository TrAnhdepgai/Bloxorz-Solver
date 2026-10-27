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
| 19_switch_lower_gate | switch | 101 | 105 | 1,039 | 108 | 89 |
| 20_split_split_lesson | switch | 2,336 | 183 | 26,903 | 2,605 | 2,324 |
| 22_split_rejoin | switch | 3,100 | 198 | 54,900 | 3,554 | 2,973 |
| 23_combined_glass_gate | combined | 108 | 107 | 238 | 127 | 37 |
| 25_combined_fragile_approach | combined | 164 | 155 | 1,032 | 177 | 89 |
| 27_combined_double_lock | combined | 310 | 307 | 16,902 | 327 | 255 |

**Thời gian tìm kiếm, ms**

| Màn | Nhóm | BFS | DFS | IDS | UCS | ASTAR |
|---|---|---:|---:|---:|---:|---:|
| 01_basic_first_steps | basic | 0.14 | 0.75 | 0.10 | 0.12 | 0.09 |
| 04_basic_step_aside | basic | 0.69 | 0.93 | 0.90 | 0.77 | 0.55 |
| 06_basic_two_rooms | basic | 1.85 | 2.26 | 14.51 | 2.30 | 1.86 |
| 08_basic_courtyard | basic | 1.91 | 1.58 | 18.42 | 2.03 | 1.79 |
| 09_fragile_orange_crossing | fragile | 1.25 | 1.09 | 14.19 | 1.53 | 1.44 |
| 11_fragile_side_by_side | fragile | 1.61 | 1.35 | 24.98 | 1.75 | 1.35 |
| 13_fragile_fragile_yard | fragile | 5.04 | 4.26 | 48.22 | 5.99 | 2.37 |
| 14_switch_soft_touch | switch | 2.81 | 2.35 | 17.86 | 3.38 | 2.23 |
| 16_switch_heavy_step | switch | 3.76 | 2.83 | 43.77 | 5.12 | 3.21 |
| 17_switch_two_bridges | switch | 6.94 | 4.60 | 168 | 11.51 | 9.88 |
| 19_switch_lower_gate | switch | 2.54 | 2.37 | 29.46 | 2.50 | 2.16 |
| 20_split_split_lesson | switch | 73.27 | 3.62 | 775 | 78.66 | 68.57 |
| 22_split_rejoin | switch | 77.21 | 4.63 | 1,585 | 89.01 | 79.52 |
| 23_combined_glass_gate | combined | 2.15 | 2.15 | 5.10 | 2.81 | 0.98 |
| 25_combined_fragile_approach | combined | 3.35 | 3.29 | 24.70 | 4.04 | 2.25 |
| 27_combined_double_lock | combined | 6.21 | 6.20 | 391 | 7.02 | 6.54 |

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
| 19_switch_lower_gate | switch | 30.77 | 41.98 | 25.62 | 39.64 | 48.16 |
| 20_split_split_lesson | switch | 1,033 | 105 | 980 | 1,420 | 1,264 |
| 22_split_rejoin | switch | 1,350 | 115 | 1,349 | 1,786 | 1,636 |
| 23_combined_glass_gate | combined | 37.99 | 50.95 | 26.58 | 47.77 | 29.37 |
| 25_combined_fragile_approach | combined | 46.92 | 71.01 | 38.97 | 63.55 | 63.41 |
| 27_combined_double_lock | combined | 97.72 | 144 | 73.94 | 117 | 101 |

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
| 19_switch_lower_gate | switch | 13 | 70 | 13 | 13 | 13 | 13 |
| 20_split_split_lesson | switch | 16 | 106 | 16 | 16 | 18 | 16 |
| 22_split_rejoin | switch | 19 | 130 | 19 | 19 | 19 | 19 |
| 23_combined_glass_gate | combined | 8 | 84 | 8 | 8 | 8 | 8 |
| 25_combined_fragile_approach | combined | 11 | 121 | 11 | 11 | 11 | 11 |
| 27_combined_double_lock | combined | 27 | 204 | 27 | 29 | 29 | 27 |

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
| 19_switch_lower_gate | switch | 23.00 | 112 | 23.00 | 23.00 | 23.00 | 23.00 |
| 20_split_split_lesson | switch | 21.00 | 149 | 21.00 | 21.00 | 21.00 | 21.00 |
| 22_split_rejoin | switch | 26.00 | 185 | 26.00 | 24.00 | 24.00 | 24.00 |
| 23_combined_glass_gate | combined | 16.00 | 134 | 16.00 | 16.00 | 16.00 | 16.00 |
| 25_combined_fragile_approach | combined | 19.00 | 195 | 19.00 | 19.00 | 19.00 | 19.00 |
| 27_combined_double_lock | combined | 47.00 | 322 | 47.00 | 45.00 | 45.00 | 45.00 |
