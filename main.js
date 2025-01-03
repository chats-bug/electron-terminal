// main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const WebSocket = require('ws');
const { exec } = require('child_process');
const { machineIdSync } = require('node-machine-id');


let mainWindow;
let ws;
const CLIENT_ID = machineIdSync(); 
let isConnected = false;


function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile('index.html');
    // Send client ID to renderer
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.executeJavaScript(`setClientId("${CLIENT_ID}")`);
    });
}


function connectToServer() {
    if (isConnected) return;
    
    ws = new WebSocket(`ws://localhost:8000/ws/${CLIENT_ID}`);
    isConnected = true;

    ws.on('open', () => {
        console.log('Connected to FastAPI server');
        mainWindow.webContents.executeJavaScript('updateStatus(true)');
        mainWindow.webContents.executeJavaScript('document.getElementById("toggle-connection").textContent = "Disconnect"');
    });

    ws.on('message', function incoming(message) {
        const data = JSON.parse(message);
        
        // Log the received command
        mainWindow.webContents.executeJavaScript(`
            addLogEntry(
                ${JSON.stringify(data.id)},
                ${JSON.stringify(data.command)},
                "Executing command...",
                false,
            )
        `).catch(err => console.error('Error adding log entry:', err));

        // Execute the command
        exec(data.command, (error, stdout, stderr) => {
            const response = {
                id: data.id,
                output: stdout,
                error: error ? error.message : null,
                stderr: stderr
            };

            const response_string = getResponseString(response);
            
            // Log the response
            mainWindow.webContents.executeJavaScript(`
                addLogEntry(
                    ${JSON.stringify(data.id)},
                    ${JSON.stringify(data.command)},
                    ${JSON.stringify(response_string)},
                    ${Boolean(error)}
                )
            `).catch(err => console.error('Error adding log entry:', err));

            ws.send(JSON.stringify(response));
        });
    });

    ws.on('close', () => {
        isConnected = false;
        mainWindow.webContents.executeJavaScript('updateStatus(false)');
        mainWindow.webContents.executeJavaScript('document.getElementById("toggle-connection").textContent = "Connect"');
        // Only attempt reconnect if connection wasn't manually stopped
        if (ws.intentionalClose !== true) {
            setTimeout(connectToServer, 5000);
        }
    });

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
        mainWindow.webContents.executeJavaScript('updateStatus(false)');
    });
}

function disconnectFromServer() {
    if (!ws || !isConnected) return;
    
    ws.intentionalClose = true;  // Flag to prevent auto-reconnect
    ws.close();
    isConnected = false;
    mainWindow.webContents.executeJavaScript('document.getElementById("toggle-connection").textContent = "Connect"');
}

// Add IPC handlers for renderer communication
ipcMain.handle('toggle-connection', async () => {
    if (isConnected) {
        disconnectFromServer();
        return false;
    } else {
        connectToServer();
        return true;
    }
});

app.whenReady().then(() => {
    createWindow();
    connectToServer();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});


function getResponseString(response) {
    let response_string = `||--------------||--------------||--------------||
                      OUTPUT
||--------------||--------------||--------------||

${response.output}`

            if (response.error) {
                response_string += `
||--------------||--------------||--------------||
                      ERROR
||--------------||--------------||--------------||

${response.error}`
            }

            if (response.stderr) {
                response_string += `
||--------------||--------------||--------------||
                      STDERR
||--------------||--------------||--------------||

${response.stderr}`
            }

    return response_string;
}