import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

interface HighlightPopupProps {
  comment?: { text: string; emoji: string };
  onConfirm: (comment: { text: string; emoji: string }) => void;
  onDelete?: () => void;
}

const EMOJI_OPTIONS = ["😀", "💡", "❗", "⭐", "🔥", "💪", "👍", "❤️", "🎯", "📌"];

const HighlightPopup = ({ comment, onConfirm, onDelete }: HighlightPopupProps) => {
  const [text, setText] = useState(comment?.text || "");
  const [selectedEmoji, setSelectedEmoji] = useState(comment?.emoji || "📌");

  if (comment?.text && onDelete) {
    return (
      <Card className="w-[200px] shadow-lg">
        <CardContent className="p-3 relative">
          <p className="text-sm">
            {comment.emoji} {comment.text}
          </p>
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-2 top-2 h-6 w-6"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
          >
            <span className="text-sm">×</span>
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-[300px] shadow-lg">
      <CardContent className="p-4 space-y-4">
        <div className="flex gap-2 items-center">
          <div className="flex gap-1 flex-wrap">
            {EMOJI_OPTIONS.map((emoji) => (
              <Button
                key={emoji}
                variant={selectedEmoji === emoji ? "secondary" : "ghost"}
                size="icon"
                className="h-8 w-8"
                onClick={() => setSelectedEmoji(emoji)}
              >
                {emoji}
              </Button>
            ))}
          </div>
        </div>
        <div className="space-y-2">
          <Input placeholder="코멘트를 입력하세요" value={text} onChange={(e) => setText(e.target.value)} />
        </div>
        <div className="flex justify-end">
          <Button onClick={() => onConfirm({ text, emoji: selectedEmoji })} disabled={!text.trim()}>
            확인
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default HighlightPopup;
