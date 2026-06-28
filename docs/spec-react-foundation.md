# React 前端基礎重整規格

## 目標

以現有 React 18、TypeScript、Vite 前端作為唯一正式 Web 前端，保留 Cloudflare Worker API 與使用者資料格式，建立可重現的開發、測試、建置及部署流程。

## 技術棧與指令

- 開發：`cd flet_app && npm run dev`
- Lint：`cd flet_app && npm run lint`
- 測試：`cd flet_app && npm test`
- 建置：`cd flet_app && npm run build`
- Worker 驗證：`node --check worker/index.js`
- Worker 安全測試：`python -m unittest tests.test_worker_security`

## 專案結構

- `flet_app/src/`：正式 React 應用程式
- `flet_app/src/components/`：相機、圖鑑及管理介面
- `flet_app/src/services/`：API 與 IndexedDB 邊界
- `worker/`：PlantNet、Perenual 與動物資料 API
- `flet_app_old/`：歷史 Flet 實作；不得成為正式建置依賴
- `tests/`：Worker 與歷史 Python 測試

## 程式風格

- TypeScript strict mode；產品資料不得新增 `any`
- React effect 必須對稱清理瀏覽器資源
- 外部 API 回應在服務邊界以明確型別表示
- 建置與 CI 使用 lockfile，不在建置期間重建 lockfile

## 測試策略

- Vitest 驗證 React hooks、元件行為與服務 helper
- Worker 保留 Node 語法及安全邊界測試
- CI 必須執行前端 lint、test、build 與 Worker 檢查

## 邊界

- 永遠：保留 Worker API 契約與 IndexedDB schema 相容性
- 先確認：刪除歷史 Flet 原始碼、改變公開 API 或資料 schema
- 禁止：提交 secrets、`node_modules`、瀏覽器 profile 或建置產物

## 成功條件

1. `npm run lint`、`npm test`、`npm run build` 全數成功。
2. 相機元件卸載時停止取得到的所有 tracks；錯誤路徑會解除 processing 狀態。
3. Cloudflare Pages 建置使用 `npm ci`，且不刪除 lockfile。
4. CI 實際驗證 React 正式前端及 Worker。
5. README 與技術棧文件正確描述 React 架構及 `VITE_API_URL`。

