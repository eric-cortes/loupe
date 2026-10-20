import { useEffect } from "react";
import { useChatStore } from "../store";
import { Topbar } from "./Topbar";
import { Hero } from "./Hero";
import { Thread } from "./Thread";
import { Composer } from "./Composer";
import { DetailPane } from "./DetailPane";

export function ChatPage() {
  const turns = useChatStore((s) => s.turns);

  useEffect(() => {
    window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  }, [turns]);

  return (
    <>
      <Topbar />
      <Hero />
      <div className="pb-40">
        <Thread />
        <Composer />
      </div>
      <DetailPane />
    </>
  );
}
