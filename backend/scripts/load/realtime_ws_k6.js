import ws from 'k6/ws';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    realtime_ws_connections: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 50 },
        { duration: '30s', target: 150 },
        { duration: '30s', target: 300 },
        { duration: '20s', target: 0 },
      ],
      gracefulRampDown: '10s',
    },
  },
  thresholds: {
    checks: ['rate>0.99'],
  },
};

const WS_URL = __ENV.WS_URL || 'ws://127.0.0.1:8000/ws/item-live-updates?token=cashier-demo&branch_id=main';

export default function () {
  const response = ws.connect(WS_URL, {}, (socket) => {
    let handshakeReceived = false;

    socket.on('open', () => {
      socket.send(JSON.stringify({
        type: 'subscribe',
        events: ['item_status_changed', 'rental_settlement_finished'],
      }));
    });

    socket.on('message', (raw) => {
      const message = JSON.parse(raw);

      if (message.type === 'connection_established') {
        handshakeReceived = true;
      }

      if (message.type === 'ping') {
        socket.send(JSON.stringify({
          type: 'pong',
          timestamp: new Date().toISOString(),
        }));
      }
    });

    socket.on('error', () => {
      // k6 captures websocket errors automatically.
    });

    socket.setTimeout(() => {
      socket.close();
    }, 5000);

    socket.on('close', () => {
      check(handshakeReceived, {
        'handshake_received': (value) => value === true,
      });
    });
  });

  check(response, {
    'ws upgrade status is 101': (r) => r && r.status === 101,
  });

  sleep(1);
}
