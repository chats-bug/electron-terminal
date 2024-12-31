# Terminal Controller 🖥️

A desktop application that allows remote command execution through WebSocket connections. Built with Electron, FastAPI, and WebSocket.

## Features 🌟

- Real-time command execution
- Secure client identification
- Beautiful UI with status indicators
- Command history with timestamps
- Error handling and logging
- Cross-platform support

## Prerequisites 📋

- Python 3.8+
- Node.js 14+
- npm or yarn

## Installation 🛠️

1. Clone the repository:
```bash
git clone <repository-url>
cd terminal-controller
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
npm install
```

## Running the Application 🚀

1. Start the FastAPI server:
```bash
python main.py
```

2. In a new terminal, start the Electron app:
```bash
npm start
```

## Building for macOS 🍎

1. Ensure you have all dependencies installed:
```bash
npm install
```

2. Build the application:
```bash
npm run build -- --mac
```

The built application will be available in the `dist` folder.

## Making Requests 📡

### Get Client ID
The client ID is displayed in the Electron app's interface when connected.

### Python Example
```python
import websockets
import asyncio
import json

async def send_command(client_id: str, command: str):
    async with websockets.connect(f'ws://localhost:8000/ws/{client_id}') as websocket:
        await websocket.send(json.dumps({
            'command': command,
            'id': 'test-id'
        }))
        response = await websocket.recv()
        print(json.loads(response))

# Usage
asyncio.run(send_command('your-client-id', 'ls -la'))
```

### JavaScript/Node.js Example
```javascript
const WebSocket = require('ws');

const sendCommand = (clientId, command) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
    
    ws.on('open', () => {
        ws.send(JSON.stringify({
            command: command,
            id: 'test-id'
        }));
    });

    ws.on('message', (data) => {
        console.log(JSON.parse(data));
        ws.close();
    });
};

// Usage
sendCommand('your-client-id', 'ls -la');
```

### cURL Example
```bash
curl -X POST http://localhost:8000/execute/your-client-id \
     -H "Content-Type: application/json" \
     -d '{"command": "ls -la"}'
```

## Project Structure 📁
```
terminal-controller/
├── assets/
│   └── icon.icns
├── index.html
├── main.js
├── main.py
├── package.json
└── requirements.txt
```

## Contributing 🤝

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.
