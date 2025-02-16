import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ArrowRight, ChevronDown, Plus, X, BookmarkPlus } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Node {
  node_id: string;
  comment: string;
  annotations: Array<{
    id: number;
    fileName: string;
    pageNumber: number;
    contents: string;
    comment: string;
  }>;
}

interface RightSidebarProps {
  selectedContent: string;
  selectedComment: { text: string; emoji: string } | null;
  onHighlightSelected?: boolean;
}

const RightSidebar = ({ selectedContent, selectedComment, onHighlightSelected }: RightSidebarProps) => {
  const [similarNodes, setSimilarNodes] = useState<Node[]>([]);
  const [expandedNodeId, setExpandedNodeId] = useState<string | null>(null);
  const [isAddingNode, setIsAddingNode] = useState(false);
  const [newNodeId, setNewNodeId] = useState("");
  const [newNodeComment, setNewNodeComment] = useState("");

  useEffect(() => {
    const fetchSimilarNodes = async () => {
      if (onHighlightSelected) {
        try {
          const response = await fetch("http://localhost:5173/api/getSimilarNodes");
          const data = await response.json();
          setSimilarNodes(data.conceptNodeList);
        } catch (error) {
          console.error("Error fetching similar nodes:", error);
        }
      }
    };

    fetchSimilarNodes();
  }, [onHighlightSelected]);

  const handleNodeClick = (nodeId: string) => {
    setExpandedNodeId(expandedNodeId === nodeId ? null : nodeId);
  };

  const handleAddNode = async () => {
    if (!newNodeId || !newNodeComment) return;

    try {
      const response = await fetch("http://localhost:5173/api/addNode", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          node_id: newNodeId,
          comment: newNodeComment,
          annotations: [],
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to add node");
      }

      const newNode = await response.json();
      setSimilarNodes((prev) => [...prev, newNode]);
      setIsAddingNode(false);
      setNewNodeId("");
      setNewNodeComment("");
    } catch (error) {
      console.error("Error adding node:", error);
    }
  };

  const handleCancelAdd = () => {
    setIsAddingNode(false);
    setNewNodeId("");
    setNewNodeComment("");
  };

  const handleAddAnnotationToNode = async (nodeId: string) => {
    if (!selectedContent) return;

    try {
      // 현재 노드의 정보를 찾습니다
      const targetNode = similarNodes.find((node) => node.node_id === nodeId);
      if (!targetNode) return;

      // 새로운 어노테이션 객체를 생성합니다
      const newAnnotation = {
        id: Date.now(),
        fileName: "sample.pdf", // 실제 파일 이름으로 변경 필요
        pageNumber: 1, // 실제 페이지 번호로 변경 필요
        contents: selectedContent,
        comment: selectedComment?.text || "",
      };

      // 노드를 업데이트합니다
      const response = await fetch("http://localhost:5173/api/updateNode", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...targetNode,
          annotations: [...targetNode.annotations, newAnnotation],
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update node");
      }

      const updatedNode = await response.json();
      setSimilarNodes((prev) => prev.map((node) => (node.node_id === nodeId ? updatedNode : node)));
    } catch (error) {
      console.error("Error adding annotation to node:", error);
    }
  };

  return (
    <div className="w-[400px] h-screen border-l bg-background bg-gray-800">
      <ScrollArea className="h-full">
        <div className="p-6 space-y-6">
          {(selectedContent || selectedComment) && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">선택된 내용</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedContent && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">내용</h4>
                    <p className="text-sm text-muted-foreground bg-accent/50 p-3 rounded-md">{selectedContent}</p>
                  </div>
                )}
                {selectedComment && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">코멘트</h4>
                    <p className="text-sm text-muted-foreground">
                      {selectedComment.emoji} {selectedComment.text}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">관련 노드</CardTitle>
              {!isAddingNode && (
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsAddingNode(true)}>
                  <Plus className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent className="p-0">
              {isAddingNode && (
                <div className="p-4 border-b bg-accent/10">
                  <div className="space-y-4">
                    <div>
                      <Input
                        value={newNodeId}
                        onChange={(e) => setNewNodeId(e.target.value)}
                        placeholder="노드 ID"
                        className="mb-2 text-black placeholder:text-gray-500"
                      />
                      <Input
                        value={newNodeComment}
                        onChange={(e) => setNewNodeComment(e.target.value)}
                        placeholder="노드 설명"
                        className="text-black placeholder:text-gray-500"
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={handleCancelAdd}>
                        취소
                      </Button>
                      <Button size="sm" onClick={handleAddNode}>
                        추가
                      </Button>
                    </div>
                  </div>
                </div>
              )}
              <div className="divide-y">
                {similarNodes.map((node) => (
                  <div key={node.node_id}>
                    <div className="flex items-center justify-between w-full p-4 text-sm group">
                      <button
                        className="flex-1 flex items-center justify-between text-left"
                        onClick={() => handleNodeClick(node.node_id)}
                      >
                        <span className="font-medium">{node.comment}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            {node.annotations.length}개의 어노테이션
                          </span>
                          <ChevronDown
                            className={`h-4 w-4 transition-transform ${
                              expandedNodeId === node.node_id ? "transform rotate-180" : ""
                            }`}
                          />
                        </div>
                      </button>
                      {selectedContent && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity ml-2"
                          onClick={() => handleAddAnnotationToNode(node.node_id)}
                          title="현재 선택된 내용을 이 노드에 추가"
                        >
                          <BookmarkPlus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    {expandedNodeId === node.node_id && node.annotations.length > 0 && (
                      <div className="bg-accent/20 divide-y">
                        {node.annotations.map((annotation) => (
                          <div key={annotation.id} className="px-6 py-3">
                            <div className="text-sm mb-1">
                              <span className="text-muted-foreground">페이지 {annotation.pageNumber}</span>
                            </div>
                            <p className="text-sm mb-2">{annotation.contents}</p>
                            {annotation.comment && (
                              <p className="text-sm text-muted-foreground">{annotation.comment}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
};

export default RightSidebar;
