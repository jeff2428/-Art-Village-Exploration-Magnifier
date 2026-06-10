# 效能基線（PR3）

這份文件描述如何量測「藝素村探險放大鏡」Flet Web 的關鍵互動指標，協助我們在 PR3 之後維持流暢體驗。

## 目標指標

| 互動 | 目標 | 量測方式 |
| --- | --- | --- |
| 縮放按鈕點擊 → 鏡頭更新 | < 16 ms（單一影格） | DevTools Performance，記錄 `adjust_camera_zoom` 到下次 paint |
| 新卡片進場動畫 | 不掉幀（≥ 50 fps） | DevTools FPS meter，量測 `_animate_new_cards` 期間 |
| 圖鑑新增植物（從辨識成功到卡片可見） | < 200 ms | DevTools Network + Performance |
| 圖鑑首次開啟（pokedex 有 10 筆以上） | < 300 ms | `performance.now()` 包住 `refresh_gallery` 呼叫 |

## 量測腳本（devtools snippet）

貼到 DevTools Console 即可（搭配 `?perf=1` query string 開啟內部旗位）：

```js
// 1) 量測縮放
const t0 = performance.now();
document.querySelector('[data-testid="zoom-in"]').click();
// 等到下次 paint 後取樣
requestAnimationFrame(() => {
  const t1 = performance.now();
  console.log(`zoom-in 渲染耗時 ${(t1 - t0).toFixed(2)} ms`);
});

// 2) 量測新卡片動畫
const fpsSamples = [];
let last = performance.now();
const handle = setInterval(() => {
  const now = performance.now();
  fpsSamples.push(1000 / (now - last));
  last = now;
}, 200);
setTimeout(() => {
  clearInterval(handle);
  const avg = fpsSamples.reduce((a, b) => a + b, 0) / fpsSamples.length;
  console.log(`卡片動畫平均 fps = ${avg.toFixed(1)}`);
}, 2000);
```

## 量測記錄表

| 日期 | 環境 | zoom-in 渲染 | 新卡片 fps | 圖鑑新增 | 備註 |
| --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | Cloudflare Pages / Chrome 130 | _._ ms | _._ fps | _._ ms | PR3 前 baseline |
| YYYY-MM-DD | Cloudflare Pages / Chrome 130 | _._ ms | _._ fps | _._ ms | PR3 後（本次重構） |
| 2026-06-03 | Local Flet Web / HTTP probe | 待瀏覽器補測 | 待瀏覽器補測 | 待瀏覽器補測 | 本機 `127.0.0.1:8550` 回應 200；瀏覽器自動化受 Windows sandbox 限制，需依 `docs/qa-checklist.md` 補人工或可用瀏覽器量測 |

## 初始載入資源基線

使用 `python scripts/measure_flet_payload.py` 量測 Flet Web build 輸出與 app package。這個基線用來追蹤 Pyodide / Flet runtime / 前端 Python 套件變更對首次載入的影響。

| 日期 | requirements | build/web 總大小 | app.zip | 最大資源 | 備註 |
| --- | --- | ---: | ---: | --- | --- |
| 2026-06-10 | `flet`, `flet-camera`, `requests` | 74,260,708 bytes | 908,421 bytes | `pyodide/pyodide.asm.wasm` 10,103,326 bytes; `main.dart.js` 8,102,720 bytes; `canvaskit/canvaskit.wasm` 6,944,939 bytes | OpenCC / Pillow 不在前端 requirements；主要剩餘載入成本是 Flet/Pyodide/CanvasKit runtime |

## QA 檢視

固定功能與視覺驗收清單請見 `docs/qa-checklist.md`。效能量測完成後，將實際數字回填到上方表格，並標註桌面或行動裝置環境。

## 變更摘要（PR3）

- `apply_camera_zoom()`：保留「只更新 `camera_preview_slot`」契約。
- `adjust_camera_zoom()`：移除 `page.update()`，改為 `status.update()` + `handle_slot.update()`，避免每按一次就重繪整個頁面。
- `refresh_gallery()`：增量新增時改用 `grid.update()` + `gallery_empty_state.update()`，並在卡片上加 `animate_opacity` / `animate_offset` 走 Flet 動畫系統。
- `_animate_new_cards()`：保留 stagger 效果，但只在卡片已掛載時才呼叫 `card.update()`。
- `plant_api.compress_image()`：新增 `optimize: bool` 參數（預設 `True` 保持相容），Web 端可在上傳前以 `optimize=False` 省 CPU。

## 注意事項

- Cloudflare Pages 部署後第一次載入較慢（Pyodide + Flet runtime 冷啟動），量測時請先暖機（reload 一次後再開始）。
- 行動裝置（Android Chrome）fps 目標下修至 30 fps；桌面以 60 fps 為標竿。
- 若 Flet 動畫造成掉幀，請確認 `card.animate_*` 已正確設定，否則會 fallback 到逐張 `card.update()` 的舊路徑。
