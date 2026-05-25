import { useState, useEffect, useRef } from "react";

export function useWebSocket(url) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const destroyed = useRef(false);

  useEffect(() => {
    destroyed.current = false;

    function connect() {
      if (destroyed.current) return;
      if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (destroyed.current) { ws.close(); return; }
        setConnected(true);
      };

      ws.onmessage = (e) => {
        if (destroyed.current) return;
        try { setData(JSON.parse(e.data)); } catch {}
      };

      ws.onclose = () => {
        setConnected(false);
        if (!destroyed.current) {
          reconnectTimer.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      destroyed.current = true;
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect trigger on cleanup
        wsRef.current.close();
      }
    };
  }, [url]);

  return { data, connected };
}
