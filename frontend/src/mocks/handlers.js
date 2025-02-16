import { http } from "msw";

// 메모리에 데이터를 저장하기 위한 임시 저장소
const store = {
  annotations: [],
  nodes: [
    {
      node_id: "test_unique_node_id",
      comment: "this is test comment",
      annotations: [
        {
          id: 1,
          fileName: "sample.pdf",
          pageNumber: 1,
          contents: "this is annotation contents",
          comment: "this is annotation comment",
        },
      ],
    },
  ],
};

export const handlers = [
  // 어노테이션 추가 API
  http.post("http://localhost:5173/api/addAnnotation", async ({ request }) => {
    const body = await request.json();
    const newAnnotation = {
      id: crypto.randomUUID(),
      ...body,
    };
    store.annotations.push(newAnnotation);
    return new Response(JSON.stringify(newAnnotation), {
      status: 201,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }),

  // 어노테이션 리스트 조회 API
  http.get("http://localhost:5173/api/getAnnotations", () => {
    return new Response(JSON.stringify(store.annotations), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }),

  // 추천 노드 API
  http.get("http://localhost:5173/api/getSimilarNodes", ({ request }) => {
    // 목업에서는 간단히 모든 노드를 반환
    const similarNodes = store.nodes;

    return new Response(JSON.stringify({ conceptNodeList: similarNodes }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }),

  // 새로운 노드 추가 API
  http.post("http://localhost:5173/api/addNode", async ({ request }) => {
    const body = await request.json();
    const newNode = {
      ...body,
      annotations: body.annotations || [],
      comment: body.comment || "",
      links: body.links || [],
    };

    // node_id의 유니크 체크
    if (store.nodes.some((node) => node.node_id === newNode.node_id)) {
      return new Response(JSON.stringify({ error: "Node ID must be unique" }), {
        status: 400,
        headers: {
          "Content-Type": "application/json",
        },
      });
    }

    store.nodes.push(newNode);
    return new Response(JSON.stringify(newNode), {
      status: 201,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }),

  // 노드 업데이트 API
  http.put("http://localhost:5173/api/updateNode", async ({ request }) => {
    const body = await request.json();
    const nodeIndex = store.nodes.findIndex((node) => node.node_id === body.node_id);

    if (nodeIndex === -1) {
      return new Response(JSON.stringify({ error: "Node not found" }), {
        status: 404,
        headers: {
          "Content-Type": "application/json",
        },
      });
    }

    store.nodes[nodeIndex] = {
      ...store.nodes[nodeIndex],
      ...body,
    };

    return new Response(JSON.stringify(store.nodes[nodeIndex]), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }),
];
