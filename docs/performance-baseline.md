# 效能基準紀錄

這份文件用來記錄 Flet 版本與 `prototype/index.html` 的同條件量測結果。

## 首頁載入

使用瀏覽器 Performance 面板或 Console 讀取 mark：

- `art-village:loader-start`
- `art-village:flet-shell-ready`
- `art-village:camera-init-start`
- `art-village:camera-ready`
- `prototype:loader-start`
- `prototype:camera-init-start`
- `prototype:camera-ready`

建議每次記錄：

- 裝置與瀏覽器：
- 網路條件：
- 首次載入到 shell ready：
- 首次載入到 camera ready：
- 是否為冷快取：

## 辨識端點

Flet 卡片與 Web 原型都會顯示 Worker 回傳的 timing：

- `plantnet_ms`
- `perenual_ms`
- `total_ms`

POST 主辨識預期不等待 Perenual，成功時 `perenual.status` 先回 `pending`，再由 `GET /metadata?scientificName=...` 補資料。

建議每次記錄：

- 照片大小：
- 拍攝部位：
- POST total_ms：
- PlantNet plantnet_ms：
- Metadata perenual_ms：
- Metadata cache：hit / miss

## 判斷準則

- 如果 POST total_ms 明顯接近 PlantNet plantnet_ms，代表端點已不再被 Perenual 二次查詢阻塞。
- 如果 Flet 首頁到 shell ready 遠慢於 prototype，才進一步評估前端框架遷移。
