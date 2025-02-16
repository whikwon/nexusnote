import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight, Pencil, Search, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { IHighlight } from "react-pdf-highlighter";
import LucideIcon from "../icon/icon";

interface LeftSidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  highlights: IHighlight[];
  onHighlightClick: (highlight: IHighlight) => void;
  onDeleteHighlight: (id: string) => void;
  setHighlightSelected: (selected: boolean) => void;
}

const MIN_WIDTH = 300;
const MAX_WIDTH = 600;

const LeftSidebar = ({
  isOpen,
  onToggle,
  highlights,
  onHighlightClick,
  onDeleteHighlight,
  setHighlightSelected,
}: LeftSidebarProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [width, setWidth] = useState(MIN_WIDTH);
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (e: MouseEvent) => {
      if (isResizing && sidebarRef.current) {
        const newWidth = e.clientX - sidebarRef.current.getBoundingClientRect().left;
        if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
          setWidth(newWidth);
        }
      }
    },
    [isResizing]
  );

  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResizing);
    }

    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    onDeleteHighlight(id);
  };

  const handleHighlightClick = (highlight: IHighlight) => {
    onHighlightClick(highlight);
    setHighlightSelected(true);
  };

  const filteredHighlights = highlights.filter(
    (highlight) =>
      highlight.content.text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      highlight.comment?.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div
      ref={sidebarRef}
      className={cn(
        "h-screen border-r relative transition-[width] duration-300 ease-in-out overflow-hidden bg-background p-[8px] bg-gray-800 flex flex-col gap-[10px]",
        isOpen ? `w-[${width}px]` : "w-[50px]",
        isResizing && "select-none"
      )}
      style={{ width: isOpen ? width : 50 }}
    >
      <Button variant="ghost" size="icon" className="w-[40px] h-[40px]" onClick={onToggle}>
        {isOpen ? (
          <LucideIcon name="ChevronLeft" className="w-4 h-4" />
        ) : (
          <LucideIcon name="ChevronRight" className="w-4 h-4" />
        )}
      </Button>

      {isOpen && (
        <>
          <div
            className="absolute right-0 top-0 w-1 h-full cursor-col-resize hover:bg-gray-300 transition-colors"
            onMouseDown={startResizing}
          />
          <div className="w-full h-[calc(100vh-50px)]">
            <div className="relative mb-4">
              <Input
                placeholder="검색"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-gray-100 w-full text-black box-border"
              />
            </div>
            <ScrollArea className="h-[calc(100vh-130px)]">
              <div className="space-y-3">
                {filteredHighlights.map((highlight) => (
                  <Card
                    key={highlight.id}
                    className="transition-colors cursor-pointer hover:bg-accent/50"
                    onClick={() => handleHighlightClick(highlight)}
                  >
                    <CardContent className="p-3 space-y-2">
                      <div className="flex items-start justify-between">
                        <h3 className="text-sm font-medium">페이지 1의 주요 내용</h3>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="w-6 h-6"
                            onClick={(e) => handleDelete(e, highlight.id)}
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="w-6 h-6">
                            <Pencil className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2">{highlight.content.text}</p>
                      {highlight.comment && (
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <span>{highlight.comment.emoji}</span>
                          <span>{highlight.comment.text}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </div>
        </>
      )}
    </div>
  );
};

export default LeftSidebar;
