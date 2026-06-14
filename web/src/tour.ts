import { driver } from "driver.js";
import "driver.js/dist/driver.css";

// Guided onboarding tour (Traditional Chinese), following the setup flow:
// blinds+stack -> players -> position -> hand -> recommendation.

export function startTour(): void {
  const tour = driver({
    showProgress: true,
    nextBtnText: "下一步",
    prevBtnText: "上一步",
    doneBtnText: "我懂了",
    progressText: "{{current}} / {{total}}",
    steps: [
      {
        element: "[data-tour='intro']",
        popover: {
          title: "歡迎使用 open-gto",
          description:
            "跟著左邊的步驟設定你的牌局,最後右邊就會告訴你這手牌的 GTO 最佳打法。完全不會打也沒關係。",
        },
      },
      {
        element: "[data-tour='blinds']",
        popover: {
          title: "① 盲注面額",
          description:
            "填你這桌的小盲 / 大盲是多少錢。這只用來把籌碼換算成「大盲(bb)」,不會影響策略本身。",
        },
      },
      {
        element: "[data-tour='stack']",
        popover: {
          title: "② 你的有效籌碼",
          description:
            "填你手上還有多少錢,系統會換算成幾個大盲(bb)。這才是 GTO 真正在意的數字。",
        },
      },
      {
        element: "[data-tour='players']",
        popover: {
          title: "③ 牌桌人數",
          description: "目前支援單挑(2 人);6Max / 9Max 多人桌正在開發中。",
        },
      },
      {
        element: "[data-tour='position']",
        popover: {
          title: "④ 你的位置",
          description:
            "選你坐在小盲還是大盲。位置不同,該怎麼打差很多 —— 這也決定了你面對的情境。",
        },
      },
      {
        element: "[data-tour='hand']",
        popover: {
          title: "⑤ 你的手牌",
          description: "選你拿到的兩張牌(點數 + 花色)。",
        },
      },
      {
        element: "[data-tour='verdict']",
        popover: {
          title: "GTO 建議出爐",
          description:
            "這裡用白話告訴你:這手牌該「全下」還是「蓋牌」,以及換算成實際金額。",
        },
      },
      {
        element: "[data-tour='grid']",
        popover: {
          title: "完整範圍表",
          description:
            "想看全貌就看這張 169 起手牌表:紅=該進攻、藍=該蓋牌。點任一格,上面的建議會跟著更新。",
        },
      },
    ],
  });
  tour.drive();
}
