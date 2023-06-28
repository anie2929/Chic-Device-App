document.addEventListener("DOMContentLoaded", function() {
    // Get the necessary DOM elements
    const startButton = document.getElementById("startButton");
    const endButton = document.getElementById("endButton");
    const waveformCanvas = document.getElementById("waveformCanvas");
  
    // Create the audio context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    let analyzerNode;
    let sourceNode;
    let websocket;
  
    // Create the waveform canvas context
    const waveformContext = waveformCanvas.getContext("2d");
  
    // Function to draw the waveform on the canvas
    function drawWaveform() {
      const bufferLength = analyzerNode.fftSize;
      const dataArray = new Uint8Array(bufferLength);
  
      analyzerNode.getByteTimeDomainData(dataArray);
  
      waveformContext.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
      waveformContext.strokeStyle = "red";
      waveformContext.lineWidth = 2;
      waveformContext.beginPath();
  
      const sliceWidth = waveformCanvas.width / bufferLength;
      let x = 0;
  
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * waveformCanvas.height) / 2;
  
        if (i === 0) {
          waveformContext.moveTo(x, y);
        } else {
          waveformContext.lineTo(x, y);
        }
  
        x += sliceWidth;
      }
  
      waveformContext.lineTo(waveformCanvas.width, waveformCanvas.height / 2);
      waveformContext.stroke();
  
      requestAnimationFrame(drawWaveform);
    }
  
    // Event listener for the start button
    startButton.addEventListener("click", function() {
      // Request access to the microphone
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
          // Create the analyzer node
          analyzerNode = audioContext.createAnalyser();
          analyzerNode.fftSize = 2048;
  
          // Create the source node
          sourceNode = audioContext.createMediaStreamSource(stream);
          sourceNode.connect(analyzerNode);
  
          // Start drawing the waveform
          audioContext.resume().then(() => {
            drawWaveform();
          });
        })
        .catch(function(error) {
          console.log('Error accessing microphone:', error);
        });
    });
  
    // Event listener for the end button
    endButton.addEventListener("click", function() {
      if (sourceNode) {
        sourceNode.disconnect();
        sourceNode = null;
      }
  
      if (analyzerNode) {
        analyzerNode.disconnect();
        analyzerNode = null;
      }
  
      if (websocket) {
        websocket.close();
        websocket = null;
      }
  
      // Process the audio data as needed
      console.log("Audio recording ended.");
    });
  
    // WebSocket connection
function setupWebSocket() {
    websocket = new WebSocket("ws://127.0.0.1:5000/socket");
  
    websocket.onopen = function() {
      console.log("WebSocket connection established.");
    };
  
    websocket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      // Process the received audio data
      console.log("Received audio data:", data);
    };
  
    websocket.onclose = function() {
      console.log("WebSocket connection closed.");
    };
  }
  
  // Call the setupWebSocket function to establish the WebSocket connection
  setupWebSocket();
  
  });
  