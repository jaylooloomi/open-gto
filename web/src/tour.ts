import { driver } from "driver.js";
import "driver.js/dist/driver.css";

// Guided onboarding tour (Traditional Chinese) for first-time / unsure users.
// Steps target [data-tour] attributes that exist once a solve has loaded.

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
            "這個工具會用 AI(博弈論最優解)告訴你:在單挑德州撲克裡,每手牌「最該怎麼打」。完全不會打也沒關係,跟著走就行。",
        },
      },
      {
        element: "[data-tour='stack']",
        popover: {
          title: "① 先設定籌碼深度",
          description:
            "拖動滑桿選你和對手的籌碼有多少個「大盲(bb)」。籌碼越淺,越多牌值得全下。",
        },
      },
      {
        element: "[data-tour='solve']",
        popover: {
          title: "② 算出最佳策略",
          description:
            "按這顆按鈕,AI 會即時算出 GTO 最佳打法。(一進來就先幫你算好 10bb 的範例了)",
        },
      },
      {
        element: "[data-tour='lookup']",
        popover: {
          title: "③ 查你手上的牌(新手看這裡)",
          description:
            "選你拿到的兩張牌,下方會直接用白話告訴你:該「全下」還是「蓋牌」。這就是最快上手的方式。",
        },
      },
      {
        element: "[data-tour='freq']",
        popover: {
          title: "整體進攻比例",
          description:
            "這條顯示:在所有起手牌裡,GTO 會推注 / 蓋牌的比例各佔多少。",
        },
      },
      {
        element: "[data-tour='view']",
        popover: {
          title: "切換角色視角",
          description:
            "看「小盲該推哪些牌」,或「大盲面對全下時該跟注哪些牌」。",
        },
      },
      {
        element: "[data-tour='grid']",
        popover: {
          title: "169 種起手牌一覽",
          description:
            "這張表是所有起手牌組合。紅色=該進攻、藍色=該蓋牌,格子裡的數字是進攻機率。點任一格,上面就會顯示那手牌的建議。",
        },
      },
    ],
  });
  tour.drive();
}
