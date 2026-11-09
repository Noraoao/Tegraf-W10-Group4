#include <bits/stdc++.h>
using namespace std;

int main(){
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int M, N;
    cin >> M >> N;

    vector<vector<long long>> cost(M, vector<long long>(N));
    for (int i = 0; i < M; i++)
        for (int j = 0; j < N; j++)
            cin >> cost[i][j];

    vector<long long> supply(M), demand(N);
    for (int i = 0; i < M; i++) cin >> supply[i];
    for (int j = 0; j < N; j++) cin >> demand[j];

    vector<bool> rowDone(M, false), colDone(N, false);
    int rowsLeft = M, colsLeft = N;
    long long totalCost = 0;
    const long long INF = LLONG_MAX / 2;

    // Modified LCM: pada setiap iterasi, pilih baris/kolom dengan
    // "opportunity cost" (penalty) terbesar -> baru cari cost termurah
    // di dalam baris/kolom terpilih (mirip Vogel's Approximation Method).
    while (rowsLeft > 0 && colsLeft > 0) {
        long long bestPenalty = -1;
        int bestType = -1; // 0 = baris, 1 = kolom
        int bestIdx = -1;

        // Hitung penalty tiap baris aktif
        for (int i = 0; i < M; i++) {
            if (rowDone[i]) continue;
            long long min1 = INF, min2 = INF;
            for (int j = 0; j < N; j++) {
                if (colDone[j]) continue;
                long long c = cost[i][j];
                if (c < min1) { min2 = min1; min1 = c; }
                else if (c < min2) min2 = c;
            }
            long long penalty = (min2 == INF) ? min1 : (min2 - min1);
            if (penalty > bestPenalty) {
                bestPenalty = penalty; bestType = 0; bestIdx = i;
            }
        }

        // Hitung penalty tiap kolom aktif
        for (int j = 0; j < N; j++) {
            if (colDone[j]) continue;
            long long min1 = INF, min2 = INF;
            for (int i = 0; i < M; i++) {
                if (rowDone[i]) continue;
                long long c = cost[i][j];
                if (c < min1) { min2 = min1; min1 = c; }
                else if (c < min2) min2 = c;
            }
            long long penalty = (min2 == INF) ? min1 : (min2 - min1);
            if (penalty > bestPenalty) {
                bestPenalty = penalty; bestType = 1; bestIdx = j;
            }
        }

        // Cari sel dengan cost termurah pada baris/kolom terpilih
        int selI = -1, selJ = -1;
        long long minCost = INF;
        if (bestType == 0) {
            int i = bestIdx;
            for (int j = 0; j < N; j++) {
                if (colDone[j]) continue;
                if (cost[i][j] < minCost) { minCost = cost[i][j]; selI = i; selJ = j; }
            }
        } else {
            int j = bestIdx;
            for (int i = 0; i < M; i++) {
                if (rowDone[i]) continue;
                if (cost[i][j] < minCost) { minCost = cost[i][j]; selI = i; selJ = j; }
            }
        }

        long long alloc = min(supply[selI], demand[selJ]);
        totalCost += alloc * cost[selI][selJ];
        supply[selI] -= alloc;
        demand[selJ] -= alloc;

        if (supply[selI] == 0 && demand[selJ] == 0) {
            rowDone[selI] = true; rowsLeft--;
            colDone[selJ] = true; colsLeft--;
        } else if (supply[selI] == 0) {
            rowDone[selI] = true; rowsLeft--;
        } else {
            colDone[selJ] = true; colsLeft--;
        }
    }

    cout << totalCost << endl;
    return 0;
}