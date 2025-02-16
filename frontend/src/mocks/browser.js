import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);

// 개발 환경에서만 MSW를 활성화
if (process.env.NODE_ENV === "development") {
  worker.start({
    onUnhandledRequest: "bypass", // 처리되지 않은 요청은 그대로 통과
  });
}
