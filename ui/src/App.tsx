import { useState } from "react";
import Connect from "./pages/Connect";
import Find from "./pages/Find";
import Drafts from "./pages/Drafts";
import Sent from "./pages/Sent";

export default function App() {
  const [screen, setScreen] = useState<"connect" | "find" | "drafts" | "sent">(
    "connect"
  );
  const [campaignId, setCampaignId] = useState<number | null>(null);

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <nav className="bg-white border-b border-gray-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-50 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-600 text-white font-black text-sm px-2.5 py-1 rounded">
            GENAI FUND
          </div>
          <span className="font-semibold text-gray-800 text-sm hidden sm:inline">
            FDE Outreach Prototype · X (Twitter)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {campaignId && (
            <>
              <button
                onClick={() => setScreen("find")}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ${
                  screen === "find"
                    ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                    : "border-gray-300 text-gray-700 bg-white hover:bg-gray-50"
                }`}
              >
                1. Tìm ứng viên
              </button>
              <button
                onClick={() => setScreen("drafts")}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ${
                  screen === "drafts"
                    ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                    : "border-gray-300 text-gray-700 bg-white hover:bg-gray-50"
                }`}
              >
                2. Nháp & Phê duyệt
              </button>
              <button
                onClick={() => setScreen("sent")}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ${
                  screen === "sent"
                    ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                    : "border-gray-300 text-gray-700 bg-white hover:bg-gray-50"
                }`}
              >
                3. Đã gửi & Trả lời
              </button>
            </>
          )}
          <button
            onClick={() => setScreen("connect")}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition ml-2 ${
              screen === "connect"
                ? "bg-gray-800 text-white border-gray-800"
                : "border-gray-200 text-gray-500 hover:text-gray-800 hover:bg-gray-50"
            }`}
          >
            ⚙ Cấu hình
          </button>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto p-6 space-y-6">
        {screen === "connect" ? (
          <Connect
            onConnected={(id: number) => {
              setCampaignId(id);
              setScreen("find");
            }}
          />
        ) : screen === "find" ? (
          <Find
            campaignId={campaignId!}
            onNavigateToDrafts={() => setScreen("drafts")}
          />
        ) : screen === "drafts" ? (
          <Drafts
            campaignId={campaignId!}
            onNavigateToSent={() => setScreen("sent")}
          />
        ) : (
          <Sent campaignId={campaignId!} />
        )}
      </main>
    </div>
  );
}
