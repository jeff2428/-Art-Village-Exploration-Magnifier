# 技術棧與系統架構

## 系統總覽

```text
Browser (React/Vite)
  ├─ Camera / Canvas
  ├─ IndexedDB (pokedex + images)
  └─ HTTPS
       └─ Cloudflare Worker
            ├─ PlantNet API
            ├─ Perenual API + Cache API
            └─ Animals KV
```

## 前端

正式前端位於 `flet_app/`：

- React 18：畫面與狀態
- TypeScript strict mode：靜態型別
- Vite 8：開發伺服器與 production bundle
- IndexedDB / `idb`：本機圖鑑與拍攝圖片
- Vitest 4：單元與回歸測試
- ESLint：TypeScript、React Hooks 與 refresh 規則

主要模組：

| 路徑 | 責任 |
|---|---|
| `src/App.tsx` | 頂層路由與 IndexedDB 初始化 |
| `src/components/CameraView.tsx` | 相機、截圖與辨識流程 |
| `src/components/Gallery.tsx` | 植物與動物圖鑑 |
| `src/components/Admin.tsx` | 動物資料管理 |
| `src/services/api.ts` | Worker API 契約 |
| `src/services/storage.ts` | IndexedDB schema 與存取 |

`flet_app_old/` 是歷史 Flet/Python 實作，不參與 production build。根目錄 Python 工具與舊測試只保留作相容性及遷移參考。

## API Worker

`worker/index.js` 執行於 Cloudflare Workers，負責：

- 隱藏 PlantNet、Perenual 及管理端 secrets
- 驗證 CORS、方法、MIME、圖片與 JSON payload 大小
- 代理植物辨識及 Perenual metadata
- 以 Cache API 快取 metadata
- 從 KV 讀寫動物資料
- isolate 內基本限流；嚴格全域限流需使用 Cloudflare WAF

前端公開契約：

- `POST /`：multipart 植物圖片辨識
- `GET /metadata?scientificName=...`：Perenual metadata
- `GET /animals`：動物名單
- `POST /animals/auth`：管理密碼驗證
- `PUT /animals`：更新動物名單

## 設定

| 名稱 | 所在位置 | 用途 |
|---|---|---|
| `VITE_API_URL` | 前端 build-time | Worker base URL |
| `WORKER_URL` | Pages build | `build.sh` 映射為 `VITE_API_URL` |
| `PLANTNET_API_KEY` | Worker secret | PlantNet |
| `PERENUAL_API_KEY` | Worker secret | Perenual |
| `ANIMALS_ADMIN_PASSWORD` | Worker secret | 管理端驗證 |
| `ALLOWED_ORIGIN(S)` | Worker variable | 精確 CORS 白名單 |
| `ANIMALS_KV` | Worker binding | 動物資料 |

## 建置與部署

`build.sh` 使用 lockfile 執行 `npm ci` 與 `npm run build`。輸出為 `flet_app/build/web`，之後加入：

- `/admin` 靜態管理頁
- `_headers` 安全與快取 headers
- `public/manifest.json` 與 service worker 靜態資源

CI 以 Node.js 22 執行 React lint、test、build，並另外驗證 Worker 語法與安全測試。

## 品質標準

- 所有正式前端變更必須通過 `npm run lint`、`npm test`、`npm run build`。
- 相機等瀏覽器資源必須在 React effect cleanup 釋放。
- Worker 外部輸入必須先驗證，再進入業務邏輯。
- 不提交 `node_modules`、build、瀏覽器 profile、archive 或平台 metadata。
- 公開 API、IndexedDB schema 或部署架構變更需同步更新規格與測試。
