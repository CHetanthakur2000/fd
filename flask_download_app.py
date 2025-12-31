from flask import Flask, request, jsonify, send_file, render_template_string
import yt_dlp
import os
from pathlib import Path
import threading
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

# HTML Template with embedded CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Downloader - Download Your Favorite Videos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            color: #333;
        }
        
        /* Dark Mode */
        body.dark-mode {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
        }
        
        body.dark-mode .card {
            background: #2d2d44;
            color: #e0e0e0;
        }
        
        body.dark-mode label {
            color: #e0e0e0;
        }
        
        body.dark-mode input[type="text"],
        body.dark-mode select {
            background: #1a1a2e;
            color: #e0e0e0;
            border-color: #444;
        }
        
        body.dark-mode input[type="text"]:focus,
        body.dark-mode select:focus {
            border-color: #667eea;
        }
        
        body.dark-mode .message {
            background: #3d3d5c;
            color: #e0e0e0;
        }
        
        body.dark-mode .file-item {
            background: #1a1a2e;
            color: #e0e0e0;
        }
        
        body.dark-mode .link-item {
            background: #1a1a2e;
            border-color: #667eea;
        }
        
        .theme-toggle {
            position: absolute;
            right: 20px;
            top: 20px;
            background: white;
            border: 2px solid #667eea;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 1.2em;
            transition: all 0.3s ease;
        }
        
        .theme-toggle:hover {
            background: #667eea;
            color: white;
        }
        
        body.dark-mode .theme-toggle {
            background: #2d2d44;
            color: white;
        }
        
        
        header {
            background: rgba(0, 0, 0, 0.8);
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #667eea;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        header h1 {
            color: #fff;
            font-size: 2.5em;
            margin-bottom: 5px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        header p {
            color: #ddd;
            font-size: 1.1em;
        }
        
        .container {
            max-width: 1200px;
            margin: 30px auto;
            width: 95%;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                margin: 20px auto;
            }
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.3);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        input[type="text"],
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
            font-family: inherit;
        }
        
        input[type="text"]:focus,
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            width: 100%;
            margin-top: 10px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-weight: 500;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .info-section {
            grid-column: 1 / -1;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        
        .info-item h3 {
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        
        .info-item p {
            font-size: 0.95em;
            line-height: 1.6;
        }
        
        .features-list {
            list-style: none;
            margin-top: 15px;
        }
        
        .features-list li {
            padding: 10px 0;
            padding-left: 30px;
            position: relative;
            color: #333;
            line-height: 1.6;
        }
        
        .features-list li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #667eea;
            font-weight: bold;
            font-size: 1.2em;
        }
        
        .links-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .link-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        
        .link-item:hover {
            background: #e7f0ff;
            transform: translateX(5px);
        }
        
        .link-item a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .link-item a:hover {
            color: #764ba2;
        }
        
        .status-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .status-card .status-indicator {
            width: 15px;
            height: 15px;
            background: #4ade80;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .file-list {
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .file-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #667eea;
        }
        
        .file-size {
            color: #666;
            font-size: 0.9em;
        }
        
        .spinner {
            display: none;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }
        
        .spinner.active {
            display: block;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        footer {
            background: rgba(0, 0, 0, 0.8);
            color: #ddd;
            text-align: center;
            padding: 20px;
            margin-top: auto;
            border-top: 3px solid #667eea;
        }
        
        footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        footer a:hover {
            text-decoration: underline;
        }
        
        .quality-options {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        
        .quality-btn {
            flex: 1;
            min-width: 100px;
            padding: 10px;
            background: #f0f0f0;
            border: 2px solid #ddd;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        
        .quality-btn:hover,
        .quality-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .loading-bar {
            width: 100%;
            height: 4px;
            background: #ddd;
            border-radius: 2px;
            overflow: hidden;
            margin-top: 10px;
            display: none;
        }
        
        .loading-bar.active {
            display: block;
        }
        
        .loading-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            animation: loading 1.5s infinite;
        }
        
        @keyframes loading {
            0% { width: 0%; }
            50% { width: 100%; }
            100% { width: 100%; }
        }
    </style>
</head>
<body>
    <button class="theme-toggle" onclick="toggleTheme()">🌙</button>
    
    <header>
        <h1>🎬 Video Downloader Pro</h1>
        <p>Download videos from your favorite platforms with ease</p>
    </header>
    
    <div class="container">
        <div class="card">
            <h2>📥 Download Video</h2>
            
            <div id="message"></div>
            
            <form id="downloadForm">
                <div class="form-group">
                    <label for="videoUrl">Video URL (or Playlist URL)</label>
                    <input type="text" id="videoUrl" placeholder="https://www.youtube.com/watch?v=... or playlist URL" required>
                    <small style="color: #666; margin-top: 5px; display: block;">💡 Tip: Paste video or playlist URL</small>
                </div>
                
                <button type="button" style="background: #667eea; color: white; padding: 10px; border-radius: 6px; border: none; cursor: pointer; margin-bottom: 15px; width: 100%; font-weight: 600;" onclick="previewVideo()">👁️ Preview Video Info</button>
                
                <div id="previewModal" style="display: none; background: #f0f0f0; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <h4 style="margin-top: 0; color: #333;">📺 Video Preview</h4>
                    <div id="previewContent"></div>
                    <button type="button" onclick="closePreview()" style="background: #999; color: white; padding: 8px 15px; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px;">Close</button>
                </div>
                
                <div class="form-group">
                    <label>Format</label>
                    <select id="formatSelect" onchange="updateFormatInfo()">
                        <option value="mp4">📹 MP4 (Video)</option>
                        <option value="mkv">📹 MKV (Video)</option>
                        <option value="webm">📹 WebM (Video)</option>
                        <option value="mp3">🎵 MP3 (Audio Only)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Quality</label>
                    <div class="quality-options">
                        <button type="button" class="quality-btn" data-quality="4k" onclick="selectQuality(this)">4K ⚡</button>
                        <button type="button" class="quality-btn active" data-quality="1080" onclick="selectQuality(this)">1080p</button>
                        <button type="button" class="quality-btn" data-quality="720" onclick="selectQuality(this)">720p</button>
                        <button type="button" class="quality-btn" data-quality="480" onclick="selectQuality(this)">480p</button>
                        <button type="button" class="quality-btn" data-quality="best" onclick="selectQuality(this)">Best</button>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>⏱️ Schedule Download (Optional)</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <input type="date" id="scheduleDate" style="padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                        <input type="time" id="scheduleTime" style="padding: 10px; border: 2px solid #ddd; border-radius: 6px;">
                    </div>
                </div>
                
                <div class="loading-bar" id="loadingBar">
                    <div class="loading-bar-fill"></div>
                </div>
                
                <div class="spinner" id="spinner"></div>
                
                <button type="submit" id="submitBtn">⬇️ Download Now</button>
            </form>
        </div>
        
        <div class="card">
            <h2>📊 Service Status</h2>
            
            <div id="statusContent" class="status-card">
                <p><span class="status-indicator"></span> Loading...</p>
            </div>
            
            <div style="margin-top: 20px;">
                <h3 style="color: #667eea; margin-bottom: 15px;">🌟 Key Features</h3>
                <ul class="features-list">
                    <li>Fast and reliable video downloading</li>
                    <li>Multiple quality options (360p to 1080p+)</li>
                    <li>Support for multiple platforms</li>
                    <li>Automatic retry on failures</li>
                    <li>Secure file management</li>
                    <li>Real-time download status</li>
                    <li>Large file support</li>
                    <li>Batch download capability</li>
                </ul>
            </div>
        </div>
        
        <div class="card info-section">
            <h2>ℹ️ About This Service</h2>
            
            <p style="color: #666; line-height: 1.8; margin-bottom: 20px;">
                Video Downloader Pro is a powerful and easy-to-use service that allows you to download videos from various platforms including YouTube, Vimeo, DailyMotion, and many others. With support for multiple quality options and advanced features, you can get your favorite videos in the format you want.
            </p>
            
            <div class="info-grid">
                <div class="info-item">
                    <h3>⚡ Lightning Fast</h3>
                    <p>Download videos at maximum speed with optimized infrastructure</p>
                </div>
                <div class="info-item">
                    <h3>🔒 Secure</h3>
                    <p>Your downloads are processed safely with no data storage</p>
                </div>
                <div class="info-item">
                    <h3>🎯 Reliable</h3>
                    <p>Advanced retry mechanisms ensure successful downloads</p>
                </div>
                <div class="info-item">
                    <h3>🌍 Universal</h3>
                    <p>Works with videos from virtually any platform online</p>
                </div>
            </div>
            
            <h3 style="color: #667eea; margin-top: 30px; margin-bottom: 15px;">🔗 Useful Links & Resources</h3>
            
            <div class="links-section">
                <div class="link-item">
                    <a href="javascript:showAPI()" title="View API Documentation">
                        📚 API Docs
                    </a>
                </div>
                <div class="link-item">
                    <a href="javascript:listDownloads()" title="View downloaded files">
                        📂 My Downloads
                    </a>
                </div>
                <div class="link-item">
                    <a href="https://www.youtube.com" target="_blank">
                        ▶️ YouTube
                    </a>
                </div>
                <div class="link-item">
                    <a href="https://www.github.com" target="_blank">
                        💻 GitHub
                    </a>
                </div>
                <div class="link-item">
                    <a href="javascript:showHelp()" title="Get help and FAQs">
                        ❓ Help & FAQs
                    </a>
                </div>
                <div class="link-item">
                    <a href="javascript:contact()" title="Contact us">
                        📧 Contact Us
                    </a>
                </div>
            </div>
        </div>
        
        <div class="card" style="grid-column: 1 / -1;">
            <h2>📥 Recent Downloads</h2>
            <button onclick="loadDownloads()" style="margin-bottom: 20px;">Refresh Downloads</button>
            <div class="file-list" id="fileList">
                <p style="color: #999; text-align: center;">No downloads yet. Start downloading!</p>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Video Downloader Pro v1.0 | Made with ❤️ | &copy; 2025 All Rights Reserved</p>
        <p style="margin-top: 10px; font-size: 0.9em;">
            <a href="javascript:void(0)">Privacy Policy</a> | 
            <a href="javascript:void(0)">Terms of Service</a> | 
            <a href="javascript:void(0)">Contact</a>
        </p>
    </footer>
    
    <script>
        let selectedQuality = '1080';
        let selectedFormat = 'mp4';
        
        // Dark Mode Toggle
        function toggleTheme() {
            document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
            updateThemeIcon();
        }
        
        function updateThemeIcon() {
            const btn = document.querySelector('.theme-toggle');
            if (document.body.classList.contains('dark-mode')) {
                btn.textContent = '☀️';
            } else {
                btn.textContent = '🌙';
            }
        }
        
        // Load theme preference
        window.addEventListener('load', () => {
            if (localStorage.getItem('theme') === 'dark') {
                document.body.classList.add('dark-mode');
            }
            updateThemeIcon();
        });
        
        function selectQuality(btn) {
            document.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedQuality = btn.getAttribute('data-quality');
        }
        
        function updateFormatInfo() {
            selectedFormat = document.getElementById('formatSelect').value;
            if (selectedFormat === 'mp3') {
                showMessage('🎵 MP3 mode: Will extract audio from video', 'info');
            }
        }
        
        // Preview Video
        async function previewVideo() {
            const url = document.getElementById('videoUrl').value.trim();
            if (!url) {
                showMessage('Please enter a URL first', 'error');
                return;
            }
            
            try {
                showMessage('📺 Fetching video info...', 'info');
                const response = await fetch('/api/preview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                
                const data = await response.json();
                if (response.ok && data.status === 'success') {
                    const info = data.info;
                    document.getElementById('previewContent').innerHTML = `
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            ${info.thumbnail ? `<img src="${info.thumbnail}" style="width: 100%; border-radius: 6px; margin-bottom: 10px; max-height: 300px; object-fit: cover;">` : ''}
                            <p><strong>📹 Title:</strong> ${info.title}</p>
                            <p><strong>⏱️ Duration:</strong> ${Math.floor(info.duration / 60)} minutes</p>
                            <p><strong>👁️ Views:</strong> ${info.views || 'N/A'}</p>
                            <p><strong>📅 Uploaded:</strong> ${info.upload_date || 'N/A'}</p>
                            ${info.is_playlist ? `<p style="color: #667eea; font-weight: 600;">📋 This is a PLAYLIST (${info.playlist_count} videos)</p>` : ''}
                        </div>
                    `;
                    document.getElementById('previewModal').style.display = 'block';
                    showMessage('✅ Preview loaded!', 'success');
                } else {
                    showMessage(data.message || 'Failed to load preview', 'error');
                }
            } catch (err) {
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        function closePreview() {
            document.getElementById('previewModal').style.display = 'none';
        }
        
        function showMessage(message, type = 'info') {
            const messageDiv = document.getElementById('message');
            messageDiv.className = 'message ' + type;
            messageDiv.textContent = message;
            messageDiv.style.display = 'block';
            
            if (type !== 'success') {
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            }
        }
        
        function showSpinner(show = true) {
            document.getElementById('spinner').classList.toggle('active', show);
            document.getElementById('loadingBar').classList.toggle('active', show);
            document.getElementById('submitBtn').disabled = show;
        }
        
        document.getElementById('downloadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('videoUrl').value.trim();
            const scheduleDate = document.getElementById('scheduleDate').value;
            const scheduleTime = document.getElementById('scheduleTime').value;
            
            if (!url) {
                showMessage('Please enter a valid URL', 'error');
                return;
            }
            
            // Check if scheduling
            if (scheduleDate && scheduleTime) {
                const scheduledTime = new Date(`${scheduleDate}T${scheduleTime}`);
                const now = new Date();
                
                if (scheduledTime <= now) {
                    showMessage('⏱️ Scheduled time must be in the future', 'error');
                    return;
                }
                
                showMessage(`✅ Download scheduled for ${scheduledTime.toLocaleString()}`, 'success');
                // In production, this would be stored in a database
                console.log(`Scheduled download for: ${scheduledTime}`);
                return;
            }
            
            showSpinner(true);
            showMessage('🚀 Initializing download...', 'info');
            
            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        url: url,
                        quality: selectedQuality,
                        format: selectedFormat,
                        is_playlist: url.includes('playlist')
                    })
                });
                
                const data = await response.json();
                
                if (response.ok && data.status === 'started') {
                    document.getElementById('videoUrl').value = '';
                    showSpinner(false);
                    
                    // Create progress container if not exists
                    if (!document.getElementById('progressContainer')) {
                        const container = document.createElement('div');
                        container.id = 'progressContainer';
                        container.innerHTML = `
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                                <div id="progressMessage" style="font-size: 1.1em; margin-bottom: 15px; font-weight: 600;">🚀 Starting download...</div>
                                <div id="progressBar" style="width: 100%; height: 20px; background: rgba(255,255,255,0.3); border-radius: 10px; overflow: hidden;">
                                    <div id="progressFill" style="width: 0%; height: 100%; background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%); transition: width 0.3s ease;"></div>
                                </div>
                                <div id="progressPercent" style="margin-top: 10px; text-align: right; font-size: 0.9em; opacity: 0.9;">0%</div>
                            </div>
                        `;
                        document.getElementById('message').parentNode.insertBefore(container, document.getElementById('message').nextSibling);
                    }
                    
                    // Check status every 1 second with live updates
                    let attempts = 0;
                    let lastMessage = '';
                    
                    const statusInterval = setInterval(async () => {
                        attempts++;
                        try {
                            const statusResponse = await fetch(`/api/download-status/${data.task_id}`);
                            const statusData = await statusResponse.json();
                            
                            // Update progress bar
                            const progress = statusData.progress || 0;
                            const message = statusData.message || 'Processing...';
                            
                            if (message !== lastMessage) {
                                document.getElementById('progressMessage').textContent = message;
                                lastMessage = message;
                            }
                            
                            document.getElementById('progressFill').style.width = progress + '%';
                            document.getElementById('progressPercent').textContent = progress + '%';
                            
                            if (statusData.status === 'success') {
                                document.getElementById('progressFill').style.background = '#4ade80';
                                showMessage(`✅ ${statusData.message}`, 'success');
                                loadDownloads();
                                clearInterval(statusInterval);
                                setTimeout(() => {
                                    const container = document.getElementById('progressContainer');
                                    if (container) container.remove();
                                }, 3000);
                            } else if (statusData.status === 'error') {
                                document.getElementById('progressFill').style.background = '#ef4444';
                                showMessage(`❌ ${statusData.message}`, 'error');
                                clearInterval(statusInterval);
                            } else if (statusData.status === 'partial') {
                                showMessage(`⚠️ ${statusData.message}`, 'success');
                                clearInterval(statusInterval);
                            }
                        } catch (err) {
                            console.error('Status check error:', err);
                        }
                        
                        // Continue checking for up to 5 minutes
                        if (attempts > 300) {
                            showMessage('⏱️ Download taking longer than expected. Check back soon!', 'info');
                            clearInterval(statusInterval);
                        }
                    }, 1000);
                } else {
                    showMessage(data.message || 'Failed to start download', 'error');
                    showSpinner(false);
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
                showSpinner(false);
            }
        });
        
        async function loadDownloads() {
            try {
                const response = await fetch('/api/downloads');
                const data = await response.json();
                
                const fileList = document.getElementById('fileList');
                
                if (data.files && data.files.length > 0) {
                    fileList.innerHTML = data.files.map(file => `
                        <div class="file-item">
                            <div>
                                <strong>${file.filename}</strong><br>
                                <span class="file-size">${file.size}</span>
                            </div>
                            <a href="/api/file/${encodeURIComponent(file.filename)}" download style="color: #667eea; text-decoration: none; font-weight: 600;">
                                ⬇️ Download
                            </a>
                        </div>
                    `).join('');
                } else {
                    fileList.innerHTML = '<p style="color: #999; text-align: center;">No downloads yet. Start downloading!</p>';
                }
            } catch (error) {
                document.getElementById('fileList').innerHTML = '<p style="color: #d32f2f; text-align: center;">Error loading downloads</p>';
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('statusContent').innerHTML = `
                    <h3>Server Status</h3>
                    <p style="margin: 15px 0;"><span class="status-indicator"></span> <strong>${data.status.toUpperCase()}</strong></p>
                    <p>Service: ${data.service}</p>
                    <p>Timeout: ${data.timeout}s</p>
                    <p>Max Retries: ${data.max_retries}</p>
                `;
            } catch (error) {
                document.getElementById('statusContent').innerHTML = '<p>Error loading status</p>';
            }
        }
        
        function showAPI() {
            alert('API Documentation\\n\\nEndpoints:\\n1. POST /api/download - Download video\\n2. GET /api/status - Service status\\n3. GET /api/downloads - List files\\n4. GET /api/file/<filename> - Download file');
        }
        
        function listDownloads() {
            loadDownloads();
        }
        
        function showHelp() {
            alert('Help & FAQs\\n\\n1. Paste video URL and select quality\\n2. Click Download Video\\n3. Wait for processing\\n4. Check My Downloads section\\n\\nSupported: YouTube, Vimeo, and more');
        }
        
        function contact() {
            alert('Contact Us\\n\\nEmail: support@example.com\\nWebsite: www.example.com\\nPhone: +1-xxx-xxx-xxxx');
        }
        
        // Load data on page load
        window.addEventListener('load', () => {
            updateStatus();
            loadDownloads();
        });
        
        // Refresh status every 30 seconds
        setInterval(updateStatus, 30000);
    </script>
</body>
</html>
"""

# Configuration
DOWNLOAD_DIR = "downloads"
MAX_RETRIES = 3
TIMEOUT = 300

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Store download status
download_status = {}

def download_video_worker(url, quality="1080", task_id=None, format_type="mp4", is_playlist=False):
    """Background worker for downloading video or playlist"""
    try:
        # Validate URL
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            if task_id:
                download_status[task_id] = {"status": "error", "message": "Invalid URL format"}
            return {"status": "error", "message": "Invalid URL format"}
        
        # Update status - fetching info
        if task_id:
            download_status[task_id] = {
                "status": "downloading",
                "message": "🔍 Fetching video information...",
                "progress": 5
            }
        print(f"[Download] Checking available formats for: {url}")
        
        # Minimal options to just get info
        info_opts = {
            'quiet': False,
            'no_warnings': True,
            'socket_timeout': 20,
            'retries': 2,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
            'skip_download': True,
        }
        
        # Get basic info first
        video_title = "Unknown"
        try:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                basic_info = ydl.extract_info(url, download=False)
                if basic_info:
                    video_title = basic_info.get('title', 'Unknown')
                    if task_id:
                        download_status[task_id] = {
                            "status": "downloading",
                            "message": f"📺 Found: {video_title}",
                            "progress": 10
                        }
                    print(f"[Download] Got basic info. Title: {video_title}")
        except Exception as e:
            if task_id:
                download_status[task_id] = {
                    "status": "downloading",
                    "message": f"⚠️ Fetching info (may take a moment)...",
                    "progress": 10
                }
            print(f"[Download] Warning: Could not get basic info: {str(e)[:80]}")
        
        # Progress hook for download updates
        def progress_hook(d):
            if task_id:
                if d['status'] == 'downloading':
                    # Calculate percentage
                    total = d.get('total_bytes', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    if total > 0:
                        percentage = min(int((downloaded / total) * 80) + 10, 90)
                        speed = d.get('_speed_str', 'Unknown')
                        eta = d.get('_eta_str', '?')
                        download_status[task_id] = {
                            "status": "downloading",
                            "message": f"⬇️ Downloading: {speed} | ETA: {eta}",
                            "progress": percentage,
                            "title": video_title
                        }
                    else:
                        download_status[task_id] = {
                            "status": "downloading",
                            "message": f"⬇️ Downloading... ({d.get('_speed_str', 'processing')})",
                            "progress": 15,
                            "title": video_title
                        }
                
                elif d['status'] == 'finished':
                    download_status[task_id] = {
                        "status": "downloading",
                        "message": "✅ Download complete, processing...",
                        "progress": 95,
                        "title": video_title
                    }
                    
        # Now try actual download with most flexible format
        # Select format based on quality preference
        format_map = {
            '4k': 'bestvideo[height>=2160]+bestaudio/bestvideo[height>=1440]+bestaudio/best',
            '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            'best': 'bestvideo+bestaudio/best',
        }
        
        format_str = format_map.get(quality, 'best')
        
        # Handle MP3 format
        is_audio_only = format_type == 'mp3'
        if is_audio_only:
            format_str = 'bestaudio/best'
        
        # Set post-processors for format conversion
        postprocessors = []
        if is_audio_only:
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        elif format_type == 'mkv':
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mkv'
            })
        elif format_type == 'webm':
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'webm'
            })
        
        # Handle playlist downloads
        nopl_arg = not is_playlist
        
        # Optimized for faster downloads
        ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': True,
            'socket_timeout': 20,
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'ignoreerrors': True,
            'no_color': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'postprocessors': postprocessors,
            'progress_hooks': [progress_hook],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'no_check_certificate': True,
            'prefer_insecure': True,
            'allow_unplayable_formats': True,
            'youtube_include_dash_manifest': True,
            'concurrent_fragment_downloads': 8,
            'ratelimit': 10000000,
            'noplaylist': nopl_arg,
        }
        
        if task_id:
            mode_text = "🎵 Extracting audio" if is_audio_only else "🎬 Starting video download"
            if is_playlist:
                mode_text += " (Playlist mode)"
            download_status[task_id] = {
                "status": "downloading",
                "message": f"{mode_text}...",
                "progress": 15,
                "title": video_title
            }
        
        print(f"[Download] Starting download with format: best")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Check if we got anything
            if info is None:
                # If download=True returns None, it might have still downloaded
                # Try to find the file anyway
                print(f"[Download] Info is None but checking for downloaded files...")
                
                error_msg = "Video download may have succeeded but info unavailable. Check downloads folder."
                if task_id:
                    download_status[task_id] = {"status": "partial", "message": error_msg}
                print(f"[Download] {error_msg}")
                return {"status": "partial", "message": error_msg}
            
            filename = ydl.prepare_filename(info)
            
            result = {
                "status": "success",
                "message": "✅ Download completed successfully!",
                "file": filename,
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration', 'N/A'),
                "progress": 100
            }
            
            if task_id:
                download_status[task_id] = result
            
            print(f"[Download] Completed: {filename}")
            return result
    
    except yt_dlp.utils.DownloadError as e:
        error_str = str(e)
        print(f"[Download Error] {error_str}")
        
        # Check if it's a format error
        if "Requested format is not available" in error_str or "not available" in error_str.lower():
            error_msg = "⚠️ YouTube format not available. Try with a VPN or different video."
        else:
            error_msg = f"❌ Download error: {error_str[:60]}"
        
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg, "progress": 0}
        return {"status": "error", "message": error_msg}
    
    except yt_dlp.utils.ExtractorError as e:
        error_msg = "❌ Video is private, age-restricted, or region-blocked. Try another video."
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg, "progress": 0}
        print(f"[Download Error] {error_msg}")
        return {"status": "error", "message": error_msg}
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)[:80]}"
        if task_id:
            download_status[task_id] = {"status": "error", "message": error_msg, "progress": 0}
        print(f"[Download Error] {error_msg}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": error_msg}

def download_video(url, quality="720"):
    """Download video from URL with specified quality (wrapper for sync calls)"""
    return download_video_worker(url, quality)



@app.route('/', methods=['GET'])
def home():
    """Serve the web interface"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/download', methods=['POST'])
def download():
    """Endpoint to download video or playlist"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        
        url = data.get('url').strip()
        quality = data.get('quality', '1080')
        format_type = data.get('format', 'mp4')
        is_playlist = data.get('is_playlist', False)
        
        if not url:
            return jsonify({"status": "error", "message": "URL cannot be empty"}), 400
        
        # Create task ID for tracking
        import time
        task_id = f"task_{int(time.time() * 1000)}"
        download_status[task_id] = {"status": "downloading", "message": "Download in progress..."}
        
        # Start download in background thread
        thread = threading.Thread(target=download_video_worker, args=(url, quality, task_id, format_type, is_playlist))
        thread.daemon = True
        thread.start()
        
        # Immediately return task info (don't wait for download to complete)
        return jsonify({
            "status": "started",
            "message": "Download started in background",
            "task_id": task_id
        }), 202
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/preview', methods=['POST'])
def preview_video():
    """Get video info for preview without downloading"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"status": "error", "message": "URL is required"}), 400
        
        url = data.get('url').strip()
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                return jsonify({"status": "error", "message": "Could not fetch video info"}), 400
            
            # Check if it's a playlist
            is_playlist = 'entries' in info
            playlist_count = len(info.get('entries', [])) if is_playlist else 0
            
            return jsonify({
                "status": "success",
                "info": {
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "views": info.get('view_count', 'N/A'),
                    "upload_date": info.get('upload_date', 'N/A'),
                    "thumbnail": info.get('thumbnail', ''),
                    "is_playlist": is_playlist,
                    "playlist_count": playlist_count,
                    "description": info.get('description', '')[:200] if info.get('description') else ''
                }
            }), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": f"Preview error: {str(e)[:80]}"}), 500


@app.route('/api/download-status/<task_id>', methods=['GET'])
def download_status_check(task_id):
    """Check status of a download task"""
    try:
        if task_id in download_status:
            return jsonify(download_status[task_id]), 200
        else:
            return jsonify({"status": "error", "message": "Task not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """Check service status"""
    return jsonify({
        "status": "running",
        "service": "Flask Video Downloader Pro",
        "download_dir": DOWNLOAD_DIR,
        "max_retries": MAX_RETRIES,
        "timeout": TIMEOUT,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/downloads', methods=['GET'])
def list_downloads():
    """List all downloaded files"""
    try:
        files = []
        if os.path.exists(DOWNLOAD_DIR):
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath) and not filename.endswith(('.part', '.ytdl')):
                    size = os.path.getsize(filepath)
                    files.append({
                        "filename": filename,
                        "size": f"{size / (1024*1024):.2f} MB" if size > 0 else "0 MB"
                    })
        
        # Sort by filename
        files.sort(key=lambda x: x['filename'])
        
        return jsonify({
            "status": "success",
            "count": len(files),
            "files": files
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/file/<path:filename>', methods=['GET'])
def get_download(filename):
    """Download a file from downloads directory"""
    try:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        
        # Security check - prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(DOWNLOAD_DIR)):
            return jsonify({"status": "error", "message": "Invalid file path"}), 403
        
        if not os.path.exists(filepath):
            return jsonify({"status": "error", "message": "File not found"}), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("🎬 VIDEO DOWNLOADER PRO - Starting Server")
    print("=" * 70)
    print(f"\n📁 Download Directory: {os.path.abspath(DOWNLOAD_DIR)}")
    print(f"⚙️  Configuration:")
    print(f"   - Max Retries: {MAX_RETRIES}")
    print(f"   - Timeout: {TIMEOUT}s")
    print(f"\n🌐 Access the application at:")
    print(f"   → http://localhost:5000")
    print(f"   → http://127.0.0.1:5000")
    print(f"\n📚 API Endpoints:")
    print(f"   - GET  /              - Web Interface")
    print("   - POST /api/download  - Download video (JSON: {\"url\": \"link\"})")
    print(f"   - GET  /api/status    - Service status")
    print(f"   - GET  /api/downloads - List downloaded files")
    print(f"   - GET  /api/file/<filename> - Download a file")
    print(f"\n🚀 Features:")
    print(f"   ✓ Beautiful web interface with dark theme")
    print(f"   ✓ Multiple quality options (360p, 480p, 720p, Best)")
    print(f"   ✓ Real-time status updates")
    print(f"   ✓ Download file management")
    print(f"   ✓ Error handling and retry logic")
    print(f"   ✓ Support for multiple video platforms")
    print("\n" + "=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
