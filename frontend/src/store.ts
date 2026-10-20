import { create } from "zustand";
import { sendChat, ChatApiError } from "./api/client";
import type { Match, Turn } from "./types";

let nextId = 0;
const makeId = () => String(nextId++);

type ChatState = {
  turns: Turn[];
  sending: boolean;
  selectedMatch: Match | null;
  selectMatch: (match: Match | null) => void;
  sendMessage: (text: string) => Promise<void>;
};

export const useChatStore = create<ChatState>((set, get) => ({
  turns: [],
  sending: false,
  selectedMatch: null,

  selectMatch: (match) => set({ selectedMatch: match }),

  sendMessage: async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || get().sending) return;

    const userTurn: Turn = { id: makeId(), role: "user", content: trimmed };
    const assistantTurn: Turn = { id: makeId(), role: "assistant", content: "", loading: true };

    set({
      turns: [userTurn, assistantTurn],
      sending: true,
      selectedMatch: null,
    });

    try {
      const data = await sendChat([{ role: "user", content: trimmed }]);
      set((state) => ({
        turns: state.turns.map((t) =>
          t.id === assistantTurn.id
            ? {
                ...t,
                loading: false,
                content: data.answer,
                structured_calls: data.structured_calls,
                matches: data.matches,
              }
            : t,
        ),
      }));
    } catch (err) {
      const message = err instanceof ChatApiError ? err.message : String(err);
      const status = err instanceof ChatApiError ? err.status : 0;
      set((state) => ({
        turns: state.turns.map((t) =>
          t.id === assistantTurn.id
            ? { ...t, loading: false, error: `${status ? `Error ${status}: ` : ""}${message}` }
            : t,
        ),
      }));
    } finally {
      set({ sending: false });
    }
  },
}));
