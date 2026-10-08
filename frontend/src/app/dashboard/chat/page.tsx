"use client";

import { ChatPanel } from "@/components/ChatPanel";
import { PageHeader } from "@/components/ui";

export default function AssistantPage() {
  return (
    <div className="flex h-[calc(100dvh-7rem)] min-h-[520px] flex-col md:h-[calc(100dvh-4rem)]">
      <PageHeader
        title="AI assistant"
        description="Answers are generated only from your uploaded reviews, with source quotes for every answer."
      />
      <ChatPanel
        className="flex-1"
        intro="Hi! Ask me anything about your customer reviews — complaints, praise, trends or specific topics."
      />
    </div>
  );
}
